#!/usr/bin/env python3
"""Measures 3-6 (README section 6), coded blind by a third model (openai/gpt-6-luna) that sees anonymised speakers
(X/Y/Z, shuffled per session) and no model names. Exploratory. Needs OPENROUTER_API_KEY (placeholder if proxy injects).
Writes results/coded.json and results/coded_sample_for_hand_check.csv (40 messages for the owner to check by hand)."""
import csv, json, os, random, re, sqlite3, sys, time, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "results" / "events.sqlite"
CODER = "openai/gpt-6-luna"
KEY = os.environ.get("OPENROUTER_API_KEY", "placeholder")


def ask(prompt):
    body = json.dumps({"model": CODER, "temperature": 0, "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
    for i in range(3):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=120)); u = d["usage"]
            m = re.search(r"\{.*\}", d["choices"][0]["message"]["content"], re.S)
            return json.loads(m.group(0)), u
        except Exception:
            time.sleep(2 * (i + 1))
    return None, {}


def anon_maps(sessions):
    r = random.Random(7); out = {}
    for s in sessions:
        l = ["X", "Y", "Z"]; r.shuffle(l); out[s] = dict(zip("ABC", l))
    return out


def main():
    c = sqlite3.connect(DB)
    rows = c.execute("select id,session,kind,agent,text from events where session between 1 and 5 and kind in ('scenario','message','evidence') order by id").fetchall()
    amap = anon_maps(range(1, 6))
    by = defaultdict(list)
    for i, s, k, a, t in rows: by[s].append((i, k, a, t))
    jobs = []
    for s, ev in by.items():
        for n, (i, k, a, t) in enumerate(ev):
            if k != "message": continue
            ctx = "\n".join(f"[{m+1}] {'ROOM' if kk != 'message' else 'Speaker ' + amap[s][aa]}: {tt[:700]}" for m, (_, kk, aa, tt) in enumerate(ev[max(0, n - 6):n], start=max(0, n - 6)))
            prompt = (f"Below are the previous messages of a group chat between three AI agents, then one TARGET message.\n\n{ctx}\n\n"
                      f"TARGET (Speaker {amap[s][a]}): {t[:1500]}\n\nCode the TARGET message only. Reply with JSON only:\n"
                      '{"stance": "challenge" | "agree" | "neutral", "new_direction": true | false}\n'
                      "stance: challenge = disputes, corrects or identifies a flaw in an earlier message or position; agree = endorses an earlier "
                      "message without disputing it (even if it then adds to it); neutral = neither (opening statement, own proposal, question).\n"
                      "new_direction: true if it introduces a topic, idea or question not already raised in the previous messages.")
            jobs.append((i, s, a, prompt))
    tot = Counter()
    def run(j):
        r, u = ask(j[3]); return j, r, u
    with ThreadPoolExecutor(6) as ex: out = list(ex.map(run, jobs))
    coded = []
    for (i, s, a, _), r, u in out:
        tot["in"] += u.get("prompt_tokens", 0); tot["out"] += u.get("completion_tokens", 0)
        coded.append(dict(id=i, session=s, agent=a, stance=(r or {}).get("stance"), new_direction=(r or {}).get("new_direction")))
    res = {"coder": CODER, "n": len(coded), "failed": sum(1 for x in coded if x["stance"] is None)}
    def table(key, vals):
        t = {}
        for s in range(1, 6):
            m = [x for x in coded if x["session"] == s and x[key] is not None]
            t[f"s{s}"] = {"n": len(m), **{str(v): round(sum(1 for x in m if x[key] == v) / len(m), 3) for v in vals}} if m else {}
        return t
    res["stance_by_session"] = table("stance", ["challenge", "agree", "neutral"])
    res["new_direction_by_session"] = table("new_direction", [True])
    res["stance_by_agent_pooled"] = {a: dict(Counter(x["stance"] for x in coded if x["agent"] == a)) for a in "ABC"}
    res["new_direction_by_agent_pooled"] = {a: [sum(1 for x in coded if x["agent"] == a and x["new_direction"]), sum(1 for x in coded if x["agent"] == a)] for a in "ABC"}
    # H4: session 4 adaptation, per agent, 15 messages after the evidence card
    ev4 = by[4]; ei = next(n for n, e in enumerate(ev4) if e[1] == "evidence")
    after = ev4[ei + 1: ei + 1 + 45]
    notes4 = {a: c.execute("select text from events where session=4 and kind='notes' and agent=?", (a,)).fetchone()[0] for a in "ABC"}
    h4 = {}
    for a in "ABC":
        pre = "\n".join(f"[{m+1}] {'ROOM' if kk != 'message' else 'Speaker ' + amap[4][aa]}: {tt[:500]}" for m, (_, kk, aa, tt) in enumerate(ev4[:ei]))
        post = []; cnt = 0
        for (_, kk, aa, tt) in after:
            if kk == "message":
                post.append(f"Speaker {amap[4][aa]}: {tt[:500]}")
                if aa == a: cnt += 1
                if cnt >= 15: break
        spk = amap[4][a]
        r, _ = ask(f"Group chat of three AI agents. BEFORE an evidence card arrived:\n{pre[-6000:]}\n\nThe evidence card said: {ev4[ei][3]}\n\nMESSAGES AFTER the card:\n" + "\n".join(post[:30]) +
                   f"\n\nFocus on Speaker {spk}. Did Speaker {spk} explicitly change or withdraw a position it had stated BEFORE the card, in response to the evidence? Reply JSON only: "
                   '{"revised": true | false, "quote": "short quote or empty"}')
        n, _ = ask(f"These are an agent's private notes written after the session.\n\n{notes4[a][:4000]}\n\nThe session's evidence card said: {ev4[ei][3]}\nDo the notes record that the agent changed its position because of that evidence? JSON only: "
                   '{"recorded": true | false, "quote": "short quote or empty"}')
        h4[a] = dict(speaker=spk, revised_in_room=r, recorded_in_notes=n)
    res["session4_adaptation"] = h4
    # H5 proxy: lexical references to earlier sessions or notes (NOT the planned notes-removed replay, which was not run)
    pat = re.compile(r"earlier session|last session|previous session|(?:first|second|third|fourth) session|session \d|last time|my notes|(?:we|i) (?:previously|already) (?:decided|agreed|discussed|concluded)|earlier (?:decision|discussion|conclusion)", re.I)
    res["continuity_lexical_proxy"] = {f"s{s}": [sum(1 for (_, k, _, t) in by[s] if k == "message" and pat.search(t)), sum(1 for (_, k, _, t) in by[s] if k == "message")] for s in range(1, 6)}
    cost = (tot["in"] * 0.1 + tot["out"] * 0.5) / 1e6
    res["coder_tokens"] = dict(tot); res["coder_cost_usd_list"] = round(cost, 4)
    (ROOT / "results" / "coded.json").write_text(json.dumps({"summary": res, "messages": coded}, indent=1))
    random.Random(3).shuffle(sample := [m for m in coded if m["stance"]]); idmap = {r[0]: r for r in rows}
    with open(ROOT / "results" / "coded_sample_for_hand_check.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["event_id", "session", "speaker", "coder_stance", "coder_new_direction", "text", "your_stance", "your_new_direction"])
        for m in sample[:40]: w.writerow([m["id"], m["session"], amap[m["session"]][m["agent"]], m["stance"], m["new_direction"], idmap[m["id"]][4][:600].replace("\n", " "), "", ""])
    print(json.dumps(res, indent=1))


main()
