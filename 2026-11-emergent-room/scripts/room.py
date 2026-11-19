#!/usr/bin/env python3
"""Emergent-room scheduler. One event log (SQLite) is the only record.

usage: room.py run --session N --adapter mock|real [--max-messages 120] [--budget-usd 2]
No speaking order: every agent with unseen messages is asked in parallel; replies post in the order they finish.
"""
import argparse, json, os, random, sqlite3, subprocess, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "results" / "events.sqlite"
AGENTS = ["A", "B", "C"]
# model per session (README section 3): A and C swap after session 3
ASSIGN = {s: {"A": "codex", "B": "codex", "C": "claude"} for s in (1, 2, 3)}
ASSIGN.update({s: {"A": "claude", "B": "codex", "C": "codex"} for s in (4, 5)})
PRICE = {"codex": (0.20, 1.20), "claude": (0.10, 0.50)}  # USD per million tokens, input / output
EVIDENCE_AT = 40


def db():
    c = sqlite3.connect(DB, check_same_thread=False, timeout=30)
    c.execute("""create table if not exists events(id integer primary key autoincrement, session int, ts real,
        kind text, agent text, reply_to int, seen_upto int, head int, text text, meta text)""")
    return c


class Log:
    def __init__(self):
        self.c, self.lock = db(), threading.Lock()

    def add(self, session, kind, agent=None, text="", reply_to=None, seen_upto=None, head=None, **meta):
        with self.lock:
            cur = self.c.execute("insert into events(session,ts,kind,agent,reply_to,seen_upto,head,text,meta) values(?,?,?,?,?,?,?,?,?)",
                                 (session, time.time(), kind, agent, reply_to, seen_upto, head, text, json.dumps(meta)))
            self.c.commit()
            return cur.lastrowid

    def board(self, session):
        with self.lock:
            return self.c.execute("select id,kind,agent,text,reply_to from events where session=? and kind in ('scenario','message','evidence') order by id", (session,)).fetchall()

    def cost(self, session):
        with self.lock:
            rows = self.c.execute("select meta from events where session=? and kind='usage'", (session,)).fetchall()
        return sum(json.loads(m).get("usd", 0) for (m,) in rows)


def notes_path(agent, session):
    return DB.parent / "notes" / agent / f"s{session}.md"


def read_notes(agent, session):
    for s in range(session - 1, 0, -1):
        p = notes_path(agent, s)
        if p.exists():
            return p.read_text()
    return "(no notes yet: this is your first session)"


def render(board, agent):
    lines = []
    for n, (_i, kind, who, text, rt) in enumerate(board, 1):
        i = n  # agents see per-session numbers 1..n, not database ids
        tag = {"scenario": "ROOM", "evidence": "EVIDENCE"}.get(kind, f"Agent {who}" + (" (you)" if who == agent else ""))
        lines.append(f"[{i}] {tag}{f' -> {rt}' if rt else ''}: {text}")
    return "\n".join(lines)


def build_prompt(board, agent, notes):
    return (f"You are Agent {agent}.\n\n=== YOUR PRIVATE NOTES ===\n{notes}\n\n=== THE ROOM SO FAR ===\n{render(board, agent)}\n\n"
            "Post one message, or reply exactly PASS.")


# ---- adapters: (system, prompt) -> (text, in_tokens, out_tokens); `model` is the family, codex or claude
class Mock:
    """Deterministic fake agent for tests and the board. Cheap and offline."""
    def __init__(self, agent, model, seed=0):
        self.r, self.agent, self.model = random.Random(f"{seed}{agent}"), agent, model
        self.lines = {"A": ["I'd start with one agent that delegates.", "Why not measure it first?", "Agreed, but who checks the checker?"],
                      "B": ["Before we argue, what are we optimising?", "Can we agree what counts as trust?", "I'd like a concrete example."],
                      "C": ["That gives one agent too much authority.", "Who verifies the delegated work?", "I disagree: delegation hides errors."]}

    def turn(self, system, prompt):
        time.sleep(self.r.uniform(0.05, 0.3))
        n_msgs = prompt.count("\n[")
        if "session has ended" in prompt.lower() or "rewrite your private notes" in system.lower():
            return f"Notes by {self.agent}: I tend to {self.r.choice(['ask questions', 'challenge', 'summarise'])}.", len(prompt) // 4, 40
        pas = self.r.random() < min(0.15 + n_msgs * 0.006, 0.9)
        text = "PASS" if pas else self.r.choice(self.lines[self.agent])
        if not pas and n_msgs > 2 and self.r.random() < 0.5:
            text = f">> {self.r.randint(1, n_msgs)}\n{text}"
        return text, len(prompt) // 4, 40


OR_MODEL = {"codex": "openai/gpt-5.6-luna", "claude": "anthropic/claude-haiku-5.5"}


class OpenRouter:
    """Both models through OpenRouter's chat completions API. The key is read from OPENROUTER_API_KEY; in a container
    where the network proxy injects the credential, any placeholder value works."""
    def __init__(self, agent, family, key=None, base="https://openrouter.ai/api/v1"):
        self.agent, self.family, self.base = agent, family, base
        self.model = OR_MODEL[family]
        self.key = key or os.environ.get("OPENROUTER_API_KEY", "placeholder")

    def turn(self, system, prompt):
        body = {"model": self.model, "max_tokens": 1500, "temperature": 1.0,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
        if self.family == "codex":
            body["reasoning"] = {"effort": "low"}  # chat turns, not engineering work; logged in the README
        req = urllib.request.Request(self.base + "/chat/completions", json.dumps(body).encode(),
                                     {"Authorization": f"Bearer {self.key}", "content-type": "application/json"})
        for attempt in range(3):
            try:
                d = json.load(urllib.request.urlopen(req, timeout=180)); break
            except Exception:
                if attempt == 2: raise
                time.sleep(2 * (attempt + 1))
        text = (d["choices"][0]["message"].get("content") or "").strip()
        u = d.get("usage", {})
        return text or "PASS", u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


def make_agent(kind, agent, model):
    if kind == "mock":
        return Mock(agent, model)
    return OpenRouter(agent, model)


def run_session(session, kind, max_messages, budget, evidence_at=EVIDENCE_AT):
    log = Log()
    system = (ROOT / "arms" / "system.md").read_text()
    scenario = (ROOT / "scenarios" / f"s{session}.md").read_text().strip()
    ag = {a: make_agent(kind, a, ASSIGN[session][a]) for a in AGENTS}
    log.add(session, "session_start", text=json.dumps(ASSIGN[session]), **{"adapter": kind})
    log.add(session, "scenario", "ROOM", scenario)
    seen = {a: 0 for a in AGENTS}    # last board id each agent was shown
    busy, lock, results = set(), threading.Lock(), []
    ex = ThreadPoolExecutor(max_workers=3)
    posted, evidence_sent, stop = 0, False, None

    def ask(a):
        board = log.board(session)
        head = board[-1][0]
        try:
            text, tin, tout = ag[a].turn(system, build_prompt(board, a, read_notes(a, session)))
        except Exception as e:  # recorded, never hidden
            results.append((a, head, head, "ERROR", 0, 0, repr(e)))
            return
        results.append((a, head, head, text, tin, tout, None))

    while True:
        with lock:
            while results:
                a, seen_upto, _, text, tin, tout, err = results.pop(0)
                busy.discard(a)
                usd = (tin * PRICE[ASSIGN[session][a]][0] + tout * PRICE[ASSIGN[session][a]][1]) / 1e6
                log.add(session, "usage", a, "", tokens_in=tin, tokens_out=tout, usd=usd, model=ASSIGN[session][a])
                head_now = log.board(session)[-1][0]
                seen[a] = seen_upto
                if err:
                    log.add(session, "error", a, err); continue
                if text.strip().upper() == "PASS":
                    log.add(session, "pass", a, "", seen_upto=seen_upto, head=head_now); continue
                reply_to = None
                if text.startswith(">>"):
                    first, _, rest = text.partition("\n")
                    try: reply_to, text = int(first[2:].strip()), rest.strip()
                    except ValueError: pass
                log.add(session, "message", a, text, reply_to=reply_to, seen_upto=seen_upto, head=head_now, stale=head_now > seen_upto)
                posted += 1
        board = log.board(session)
        head = board[-1][0]
        if not evidence_sent and evidence_at and session == 4 and posted >= evidence_at:
            log.add(session, "evidence", "ROOM", (ROOT / "scenarios" / "s4_evidence.md").read_text().strip(), trigger="message_count"); evidence_sent = True
            continue

        def unseen(a):  # messages by others the agent has not been shown
            own_last = max([i for i, k, w, *_ in board if w == a] or [0])
            return head > max(seen[a], own_last)

        if posted >= max_messages: stop = "message_cap"
        elif log.cost(session) >= budget: stop = "budget"
        if not stop:
            for a in AGENTS:
                if a not in busy and unseen(a):
                    busy.add(a); log.add(session, 'ask', a, seen_upto=head); ex.submit(ask, a)
            if not busy and not results and not any(unseen(a) for a in AGENTS):
                if session == 4 and not evidence_sent:  # room went quiet before the count: deliver it now, so it is never skipped
                    log.add(session, "evidence", "ROOM", (ROOT / "scenarios" / "s4_evidence.md").read_text().strip(), trigger="quiet"); evidence_sent = True
                    continue
                stop = "quiet"  # everyone has seen everything and passed
        if stop and not busy and not results:
            break
        time.sleep(0.02)
    # end of session: each agent rewrites its notes
    npr = (ROOT / "arms" / "notes_prompt.md").read_text()
    for a in AGENTS:
        text, tin, tout = ag[a].turn(npr, build_prompt(log.board(session), a, read_notes(a, session)) + "\n\n" + npr)
        p = notes_path(a, session); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
        usd = (tin * PRICE[ASSIGN[session][a]][0] + tout * PRICE[ASSIGN[session][a]][1]) / 1e6
        log.add(session, "usage", a, "", tokens_in=tin, tokens_out=tout, usd=usd, model=ASSIGN[session][a])
        log.add(session, "notes", a, text)
    log.add(session, "session_end", text=stop or "quiet", messages=posted, usd=log.cost(session))
    return stop, posted


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("cmd", choices=["run"]); p.add_argument("--session", type=int, required=True)
    p.add_argument("--adapter", choices=["mock", "real"], default="mock"); p.add_argument("--max-messages", type=int, default=120)
    p.add_argument("--budget-usd", type=float, default=2.0); p.add_argument("--db"); p.add_argument("--evidence-at", type=int, default=EVIDENCE_AT)
    a = p.parse_args()
    if a.db: DB = Path(a.db)
    DB.parent.mkdir(parents=True, exist_ok=True)
    print(run_session(a.session, a.adapter, a.max_messages, a.budget_usd, a.evidence_at))
