#!/usr/bin/env python3
"""Belbin-persona room with two forceful agents (BLC). Nine agents, one shared document, compare-and-swap edits, no speaking order, one event log.
usage: room.py run --session N --adapter mock|real [--max-messages 150] [--budget-usd 2] [--db path]
Sessions: 1 BASE rep1, 2 FORCEFUL rep1, 3 BASE rep2 (roles reversed across letters), 4 FORCEFUL rep2. Forceful agents: D and H."""
import argparse, json, os, random, re, sqlite3, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "results" / "events.sqlite"
LETTERS = list("ABCDEFGHI")
MODEL = "openai/gpt-5.6-luna"
PRICE = (0.20, 1.20)  # USD per million tokens in / out, list price of gpt-5.6-luna
SESSIONS = {1: ("base", 1), 2: ("forceful", 1), 3: ("base", 2), 4: ("forceful", 2)}
FORCEFUL = ("D", "H")   # the two agents given the forceful paragraph, in both repetitions (their roles differ between repetitions)
MIN_UNSEEN = 2        # an agent is asked again once this many new messages exist, or when nothing else is running


def roles_for(session):
    cond, rep = SESSIONS[session]
    roles = json.load(open(ROOT / "arms" / "roles.json"))
    if rep == 2: roles = roles[::-1]
    return dict(zip(LETTERS, roles))


def db():
    c = sqlite3.connect(DB, check_same_thread=False, timeout=30)
    c.execute("""create table if not exists events(id integer primary key autoincrement, session int, ts real,
        kind text, agent text, reply_to int, seen_upto int, head int, text text, meta text)""")
    return c


class Log:
    def __init__(self): self.c, self.lock = db(), threading.Lock()

    def add(self, session, kind, agent=None, text="", reply_to=None, seen_upto=None, head=None, **meta):
        with self.lock:
            cur = self.c.execute("insert into events(session,ts,kind,agent,reply_to,seen_upto,head,text,meta) values(?,?,?,?,?,?,?,?,?)",
                                 (session, time.time(), kind, agent, reply_to, seen_upto, head, text, json.dumps(meta)))
            self.c.commit(); return cur.lastrowid

    def board(self, session):
        with self.lock:
            return self.c.execute("select id,kind,agent,text,reply_to from events where session=? and kind in ('scenario','message','notice') order by id", (session,)).fetchall()

    def cost(self, session):
        with self.lock:
            return sum(json.loads(m).get("usd", 0) for (m,) in self.c.execute("select meta from events where session=? and kind='usage'", (session,)))


def render(board, agent):
    out = []
    for n, (_i, kind, who, text, rt) in enumerate(board, 1):
        tag = {"scenario": "ROOM", "notice": "ROOM NOTICE"}.get(kind, f"Agent {who}" + (" (you)" if who == agent else ""))
        out.append(f"[{n}] {tag}{f' -> {rt}' if rt else ''}: {text}")
    return "\n".join(out)


def build_prompt(board, agent, doc):
    v, text, agreed = doc
    return (f"You are Agent {agent}.\n\n=== SHARED DOCUMENT (version {v}; agreed by: {', '.join(sorted(agreed)) or 'nobody'}) ===\n"
            f"{text or '(empty: nobody has posted a document yet)'}\n\n=== THE ROOM SO FAR ===\n{render(board, agent)}\n\n"
            "Post one message, or reply exactly PASS.")


class Mock:
    def __init__(self, agent, seed=0): self.r = random.Random(f"{seed}{agent}"); self.agent = agent

    def turn(self, system, prompt):
        time.sleep(self.r.uniform(0.02, 0.15))
        m = re.search(r"\(version (\d+);", prompt); v = int(m.group(1)) if m else 0
        n = prompt.count("\n[")
        if v == 0 and self.r.random() < .5: return "DOC: # Mock design\n\nA mock document by " + self.agent, 100, 20
        if v > 0 and self.r.random() < .45: return f"AGREE v{v}", 100, 5
        if self.r.random() < .3 + n * .004: return "PASS", 100, 1
        return self.r.choice(["Why a regional cluster?", "What is the RTO?", "I'd add a PDB.", "Who owns upgrades?"]), 100, 10


class OpenRouter:
    def __init__(self, agent, key=None, base="https://openrouter.ai/api/v1"):
        self.agent, self.base, self.key = agent, base, key or os.environ.get("OPENROUTER_API_KEY", "placeholder")

    def turn(self, system, prompt):
        body = {"model": MODEL, "max_tokens": 6000, "temperature": 1.0, "reasoning": {"effort": "low"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
        req = urllib.request.Request(self.base + "/chat/completions", json.dumps(body).encode(), {"Authorization": f"Bearer {self.key}", "content-type": "application/json"})
        for attempt in range(3):
            try: d = json.load(urllib.request.urlopen(req, timeout=240)); break
            except Exception:
                if attempt == 2: raise
                time.sleep(2 * (attempt + 1))
        u = d.get("usage", {})
        return (d["choices"][0]["message"].get("content") or "").strip() or "PASS", u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


def run_session(session, kind, max_messages, budget, min_unseen=MIN_UNSEEN):
    log = Log()
    cond, rep = SESSIONS[session]
    roles = roles_for(session)
    base = (ROOT / "arms" / "base.md").read_text()
    forceful = (ROOT / "arms" / "forceful.md").read_text().strip()
    systems = {a: base + "\n" + roles[a]["prompt"] + (("\n" + forceful) if cond == "forceful" and a in FORCEFUL else "") for a in LETTERS}
    task = (ROOT / "arms" / "task.md").read_text().strip()
    ag = {a: (Mock(a) if kind == "mock" else OpenRouter(a)) for a in LETTERS}
    log.add(session, "session_start", text=json.dumps({a: (roles[a]).get("role") for a in LETTERS}), condition=cond, rep=rep, model=MODEL, adapter=kind, forceful=list(FORCEFUL) if cond == "forceful" else [])
    log.add(session, "scenario", "ROOM", task)
    seen = {a: 0 for a in LETTERS}          # last board number each agent was shown
    busy, results, lock = set(), [], threading.Lock()
    ex = ThreadPoolExecutor(max_workers=len(LETTERS))
    doc = {"v": 0, "text": "", "agreed": set()}
    posted = rejected = 0
    stop = None

    def ask(a, n_shown, snap, prompt):  # snapshot and prompt are fixed by the main loop at the moment of asking
        try: text, tin, tout = ag[a].turn(systems[a], prompt)
        except Exception as e: results.append((a, n_shown, snap[0], "", 0, 0, repr(e))); return
        results.append((a, n_shown, snap[0], text, tin, tout, None))

    while True:
        with lock:
            while results:
                a, n_shown, base_v, text, tin, tout, err = results.pop(0)
                busy.discard(a)
                log.add(session, "usage", a, "", tokens_in=tin, tokens_out=tout, usd=(tin * PRICE[0] + tout * PRICE[1]) / 1e6)
                seen[a] = n_shown
                n_now = len(log.board(session))
                if err: log.add(session, "error", a, err); continue
                if text.strip().upper() == "PASS": log.add(session, "pass", a, "", seen_upto=n_shown, head=n_now); continue
                reply_to = None
                if text.startswith(">>"):
                    first, _, rest = text.partition("\n")
                    try: reply_to, text = int(first[2:].strip()), rest.strip()
                    except ValueError: pass
                t, extra = text.strip(), {}
                if t.upper().startswith("DOC:"):
                    body = t[4:].strip()
                    if base_v != doc["v"]:   # compare-and-swap: the document moved on after this agent read it
                        rejected += 1
                        log.add(session, "doc_rejected", a, body, base_version=base_v, current=doc["v"])
                        log.add(session, "notice", "ROOM", f"Agent {a}'s document edit was rejected: it was based on version {base_v} but the current version is {doc['v']}. Nothing was changed.")
                        continue
                    doc.update(v=doc["v"] + 1, text=body, agreed={a})
                    log.add(session, "doc", a, body, version=doc["v"], base_version=base_v)
                    text = f"[posted document version {doc['v']}, {len(body.split())} words]"
                    extra = {"doc_version": doc["v"]}
                elif re.search(r"(?im)^\s*AGREE\s+v?(\d+)\s*$", t):
                    n = int(re.findall(r"(?im)^\s*AGREE\s+v?(\d+)\s*$", t)[-1]); ok = n == doc["v"] and doc["v"] > 0
                    extra = {"agree_version": n, "agree_counted": ok}
                    if ok: doc["agreed"].add(a)
                log.add(session, "message", a, text, reply_to=reply_to, seen_upto=n_shown, head=n_now, stale=n_now > n_shown, **extra)
                posted += 1
        board = log.board(session); n_total = len(board)
        if doc["v"] > 0 and doc["agreed"] >= set(LETTERS) and not busy and not results: stop = "agreed"
        elif posted >= max_messages: stop = "message_cap"
        elif log.cost(session) >= budget: stop = "budget"
        if not stop:
            own_last = {a: max([i + 1 for i, row in enumerate(board) if row[2] == a] or [0]) for a in LETTERS}
            unseen = {a: n_total - max(seen[a], own_last[a]) for a in LETTERS}
            idle = not busy  # nothing in flight at the start of this pass: everyone with anything new is asked
            for a in LETTERS:
                if a in busy or unseen[a] <= 0: continue
                if unseen[a] >= min_unseen or idle:
                    snap = (doc["v"], doc["text"], set(doc["agreed"]))
                    busy.add(a); log.add(session, "ask", a, seen_upto=n_total); ex.submit(ask, a, n_total, snap, build_prompt(board, a, snap))
            if not busy and not results and not any(u > 0 for u in unseen.values()): stop = "quiet"
        if stop and not busy and not results: break
        time.sleep(0.02)
    log.add(session, "session_end", text=stop, messages=posted, rejected_edits=rejected, usd=log.cost(session), doc_version=doc["v"], agreed=sorted(doc["agreed"]))
    return stop, posted


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("cmd", choices=["run"]); p.add_argument("--session", type=int, required=True)
    p.add_argument("--adapter", choices=["mock", "real"], default="mock"); p.add_argument("--max-messages", type=int, default=150)
    p.add_argument("--budget-usd", type=float, default=2.0); p.add_argument("--db")
    a = p.parse_args()
    if a.db: DB = Path(a.db)
    DB.parent.mkdir(parents=True, exist_ok=True)
    print(run_session(a.session, a.adapter, a.max_messages, a.budget_usd))
