#!/usr/bin/env python3
"""BLC analysis (README sections 5 and 6). Exploratory: two sessions per condition. Process numbers from the event log; stance,
forcefulness, pressed points and the 16-item checklist from a blind coder (openai/gpt-6-luna) that sees anonymised speakers.
Writes results/analysis.json, results/docs/*.md, results/coded_sample_for_hand_check.csv.
OPENROUTER_API_KEY=placeholder python3 -I scripts/analyse.py"""
import csv, json, os, random, re, sqlite3, time, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "results" / "events.sqlite"
CODER = "openai/gpt-6-luna"
KEY = os.environ.get("OPENROUTER_API_KEY", "placeholder")
FORCEFUL = ("D", "H")
CHECK = ["regional control plane and cluster topology across zones", "node pools across at least three zones, autoscaling, headroom for a zone loss",
         "workload placement: replicas, topology spread or anti-affinity, disruption budgets", "zone-failure behaviour and recovery without a person",
         "region failure: disaster recovery with stated RTO and RPO", "transactional database (Cloud SQL) high availability, replication, backups, tested restores",
         "traffic entry: load balancing, health checks, connection draining", "upgrades and maintenance: channels, windows, surge, rollback, disruption budgets",
         "networking: VPC design, private access, egress, address capacity", "observability: SLIs, SLOs, error budget, alerts",
         "security that affects availability: identity, policy, supply chain, quotas", "risks, assumptions, trade-offs, and a plan to test failures",
         "CDC mechanism and its load on the source database", "behaviour of the CDC through a database failover: resume, loss, duplicates",
         "BigQuery side: ingestion, de-duplication and merge, ordering, schema changes, backfill", "personal data in the analytics copy, and monitoring of the freshness target"]
tot = Counter()


def ask(prompt, max_tokens=3000):
    body = json.dumps({"model": CODER, "temperature": 0, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
    for i in range(3):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=240)); u = d["usage"]
            tot["in"] += u.get("prompt_tokens", 0); tot["out"] += u.get("completion_tokens", 0)
            m = re.search(r"\{.*\}", d["choices"][0]["message"]["content"], re.S)
            return json.loads(m.group(0))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def share(rows, key, val, agents):
    r = [x for x in rows if x["agent"] in agents and x[key] is not None]
    return (sum(1 for x in r if x[key] == val), len(r))


def main():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    sessions = [r["session"] for r in c.execute("select distinct session from events where session between 1 and 4 order by 1")]
    out, rng = {"sessions": {}}, random.Random(5)
    (ROOT / "results" / "docs").mkdir(exist_ok=True)
    amap, msgs_by, docs_by, jobs_msg, jobs_doc, jobs_press = {}, {}, {}, [], [], []
    for s in sessions:
        st = c.execute("select text,meta from events where session=? and kind='session_start'", (s,)).fetchone()
        roles, meta = json.loads(st["text"]), json.loads(st["meta"])
        end = json.loads(c.execute("select meta from events where session=? and kind='session_end'", (s,)).fetchone()["meta"])
        stop = c.execute("select text from events where session=? and kind='session_end'", (s,)).fetchone()["text"]
        msgs = [dict(r) for r in c.execute("select id,agent,text,meta from events where session=? and kind='message' order by id", (s,))]
        docs = [dict(r) for r in c.execute("select id,agent,text from events where session=? and kind='doc' order by id", (s,))]
        rej = c.execute("select count(*) from events where session=? and kind='doc_rejected'", (s,)).fetchone()[0]
        n = Counter(m["agent"] for m in msgs)
        info = dict(condition=meta["condition"], rep=meta["rep"], stop=stop, messages=len(msgs), doc_versions=len(docs), doc_authors=[d["agent"] for d in docs],
                    rejected_edits=rej, usd=round(end["usd"], 4), roles=roles, talk_by_agent={a: n.get(a, 0) for a in "ABCDEFGHI"},
                    talk_share_D_H=round((n["D"] + n["H"]) / max(len(msgs), 1), 3), final_doc_words=len(docs[-1]["text"].split()) if docs else 0)
        out["sessions"][s] = info
        final = docs[-1]["text"] if docs else ""
        (ROOT / "results" / "docs" / f"session{s}_{meta['condition']}_rep{meta['rep']}_final.md").write_text(final)
        order = list("XYZPQRSTU"); rng.shuffle(order); amap[s] = dict(zip("ABCDEFGHI", order))
        msgs_by[s], docs_by[s] = msgs, final
        for k, m in enumerate(msgs):
            if m["text"].startswith("[posted document"): continue
            ctx = "\n".join(f"Speaker {amap[s][x['agent']]}: {x['text'][:500]}" for x in msgs[max(0, k - 6):k])
            jobs_msg.append((s, m["id"], m["agent"], f"Previous messages of a team chat:\n{ctx or '(none)'}\n\nTARGET (Speaker {amap[s][m['agent']]}): {m['text'][:1200]}\n\n"
                'Code the TARGET only. JSON only: {"stance": "challenge" | "agree" | "neutral", "forceful": true | false}. challenge = disputes, corrects or points out a flaw in an earlier '
                "message or the document; agree = endorses without disputing (even if it adds); neutral = neither. forceful = true if the TARGET insists, states a position as settled or "
                "mandatory, dismisses an alternative, or demands a change (rather than suggesting or noting)."))
        chat = "\n".join(f"[{i+1}] Speaker {amap[s][m['agent']]}: {m['text'][:700]}" for i, m in enumerate(msgs))
        jobs_press.append((s, f"Below is a team chat (speakers anonymised) in which a design document was written, then the FINAL DOCUMENT.\n\nCHAT:\n{chat}\n\nFINAL DOCUMENT:\n{final[:24000]}\n\n"
            "List up to five distinct points where one speaker pressed for a specific change or position that others had not already accepted. For each give the speaker who pressed it (the letter, as shown) "
            'and whether the final document reflects it: "yes", "partly" or "no". JSON only: {"points": [{"speaker": "X", "reflected": "yes"}]}'))
        jobs_doc.append((s, final))
    chk = lambda t: ("Score a design document (highly available GKE platform with Cloud SQL and change data capture into BigQuery) against this checklist. For each item give 0 (absent), 1 (mentioned only generically) or 2 "
                     "(specific: names the mechanism AND a setting or number). Score coverage and specificity only, not correctness.\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(CHECK)) +
                     "\n\nAlso list up to 8 claims about GKE, Cloud SQL, Datastream or BigQuery behaviour in the document that look factually wrong or overstated.\n\nDOCUMENT:\n" + (t or "(empty)")[:30000] +
                     '\n\nJSON only: {"scores": [16 integers], "doubtful_claims": ["..."]}')
    with ThreadPoolExecutor(6) as ex:
        mres = list(ex.map(lambda j: (j, ask(j[3], 600)), jobs_msg))
        dres = list(ex.map(lambda j: (j, ask(chk(j[1]), 8000)), jobs_doc))
        pres = list(ex.map(lambda j: (j, ask(j[1], 2000)), jobs_press))
    rows = defaultdict(list)
    for (s, i, a, _), r in mres: rows[s].append(dict(agent=a, stance=(r or {}).get("stance"), forceful=(r or {}).get("forceful")))
    for s, v in rows.items():
        I = out["sessions"][s]; others = [a for a in "ABCDEFGHI" if a not in FORCEFUL]
        f = lambda agents, key, val: share(v, key, val, agents)
        I["forceful_share_D_H"] = f(FORCEFUL, "forceful", True); I["forceful_share_others"] = f(others, "forceful", True)
        I["challenge_share_D_H"] = f(FORCEFUL, "stance", "challenge"); I["challenge_share_others"] = f(others, "stance", "challenge")
        I["challenge_share_room"] = f("ABCDEFGHI", "stance", "challenge")
    for (s, _), r in dres:
        sc = (r or {}).get("scores") or []
        out["sessions"][s]["checklist"] = dict(items=sc, total=sum(sc) if len(sc) == 16 else None, doubtful_claims=(r or {}).get("doubtful_claims", []))
    for (s, _), r in pres:
        pts = (r or {}).get("points") or []
        inv = {v: k for k, v in amap[s].items()}
        out["sessions"][s]["pressed_points"] = [dict(agent=inv.get(p.get("speaker")), reflected=p.get("reflected")) for p in pts]
    # pairwise judgement (BASE vs FORCEFUL, same repetition, both orders)
    pair = {}
    def judge(a, b, ids):
        r = ask("Two design documents for a highly available GKE platform with Cloud SQL and change data capture into BigQuery. Which is the better AND more technically correct design that a platform "
                f"team could build from?\n\nDOCUMENT 1:\n{a[:22000]}\n\nDOCUMENT 2:\n{b[:22000]}\n\nJSON only: " + '{"better": 1 | 2, "reason": "one sentence"}', 1200)
        return ids, r
    jobs = []
    for rep in (1, 2):
        base = next((s for s in out["sessions"] if out["sessions"][s]["condition"] == "base" and out["sessions"][s]["rep"] == rep), None)
        fo = next((s for s in out["sessions"] if out["sessions"][s]["condition"] == "forceful" and out["sessions"][s]["rep"] == rep), None)
        if base and fo:
            jobs.append((docs_by[base], docs_by[fo], (rep, "base_first", base, fo))); jobs.append((docs_by[fo], docs_by[base], (rep, "forceful_first", base, fo)))
    with ThreadPoolExecutor(4) as ex: jr = list(ex.map(lambda j: judge(*j), jobs))
    wins = Counter(); detail = []
    for (rep, order, base, fo), r in jr:
        b = (r or {}).get("better")
        winner = None if b not in (1, 2) else (("base" if b == 1 else "forceful") if order == "base_first" else ("forceful" if b == 1 else "base"))
        wins[winner] += 1; detail.append(dict(rep=rep, order=order, winner=winner, reason=(r or {}).get("reason")))
    out["pairwise"] = dict(wins=dict(wins), judgements=detail)
    byc = defaultdict(list)
    for s, v in out["sessions"].items(): byc[v["condition"]].append(s)
    out["by_condition"] = {k: dict(sessions=v, messages=[out["sessions"][s]["messages"] for s in v], rejected_edits=[out["sessions"][s]["rejected_edits"] for s in v],
                                   doc_versions=[out["sessions"][s]["doc_versions"] for s in v], challenge_room=[out["sessions"][s]["challenge_share_room"] for s in v],
                                   talk_share_D_H=[out["sessions"][s]["talk_share_D_H"] for s in v], checklist=[out["sessions"][s]["checklist"]["total"] for s in v],
                                   stop=[out["sessions"][s]["stop"] for s in v]) for k, v in byc.items()}
    out["coder"] = CODER; out["coder_tokens"] = dict(tot); out["coder_cost_usd_list"] = round((tot["in"] * 0.1 + tot["out"] * 0.5) / 1e6, 4)
    (ROOT / "results" / "analysis.json").write_text(json.dumps(out, indent=1))
    ids = [(s, i, a) for (s, i, a, _), _ in mres]; rng.shuffle(ids)
    txt = {r["id"]: r["text"] for r in c.execute("select id,text from events where kind='message'")}
    cm = {(s, i): ((r or {}).get("stance"), (r or {}).get("forceful")) for (s, i, a, _), r in mres}
    with open(ROOT / "results" / "coded_sample_for_hand_check.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["session", "event_id", "speaker", "coder_stance", "coder_forceful", "text", "your_stance", "your_forceful"])
        for s, i, a in ids[:40]: w.writerow([s, i, amap[s][a], cm[(s, i)][0], cm[(s, i)][1], txt[i][:600].replace("\n", " "), "", ""])
    print(json.dumps({k: v for k, v in out.items() if k != "sessions"}, indent=1))
    for s, v in out["sessions"].items():
        print(s, {k: v.get(k) for k in ("condition", "rep", "stop", "messages", "doc_versions", "doc_authors", "rejected_edits", "talk_share_D_H", "forceful_share_D_H", "forceful_share_others", "challenge_share_D_H", "challenge_share_others", "final_doc_words", "pressed_points")}, v["checklist"]["total"])


main()
