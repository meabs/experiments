#!/usr/bin/env python3
"""BLB analysis (README sections 5 and 6). Exploratory: two sessions per condition.
Process numbers come from the event log; role recognisability, challenge share and the 12-item checklist come from a blind
coder (openai/gpt-6-luna) that sees anonymised speakers. Writes results/analysis.json, results/docs/*.md and
results/coded_sample_for_hand_check.csv.   OPENROUTER_API_KEY=placeholder python3 -I scripts/analyse.py"""
import csv, json, os, random, re, sqlite3, time, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "results" / "events.sqlite"
CODER = "openai/gpt-6-luna"
KEY = os.environ.get("OPENROUTER_API_KEY", "placeholder")
ROLES = json.load(open(ROOT / "arms" / "roles.json"))
DESC = {  # short descriptions from the Belbin page (as in arms/roles.json)
    r["role"]: r["prompt"].split("this role ")[1].split(" Its strengths")[0] for r in ROLES}
CHECK = ["regional control plane and cluster topology across zones", "node pools across at least three zones, autoscaling, headroom for a zone loss",
         "workload placement: replicas, topology spread or anti-affinity, disruption budgets", "zone-failure behaviour and recovery without a person",
         "region failure: disaster recovery with stated RTO and RPO", "stateful tier: database high availability, replication, backups, tested restores",
         "traffic entry: load balancing, health checks, connection draining", "upgrades and maintenance: channels, windows, surge, rollback, disruption budgets",
         "networking: VPC design, private access, egress, address capacity", "observability: SLIs, SLOs, error budget, alerts",
         "security that affects availability: identity, policy, supply chain, quotas", "risks, assumptions, trade-offs, and a plan to test failures"]
tot = Counter()


def ask(prompt, max_tokens=1500):
    body = json.dumps({"model": CODER, "temperature": 0, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
    for i in range(3):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=180)); u = d["usage"]
            tot["in"] += u.get("prompt_tokens", 0); tot["out"] += u.get("completion_tokens", 0)
            m = re.search(r"\{.*\}", d["choices"][0]["message"]["content"], re.S)
            return json.loads(m.group(0))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def main():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    sessions = [r["session"] for r in c.execute("select distinct session from events where session between 1 and 4 order by 1")]
    out = {"sessions": {}}
    (ROOT / "results" / "docs").mkdir(exist_ok=True)
    amap = {}
    rng = random.Random(5)
    jobs_role, jobs_stance, jobs_doc = [], [], []
    for s in sessions:
        st = c.execute("select text,meta from events where session=? and kind='session_start'", (s,)).fetchone()
        roles, meta = json.loads(st["text"]), json.loads(st["meta"])
        end = json.loads(c.execute("select meta from events where session=? and kind='session_end'", (s,)).fetchone()["meta"])
        endkind = c.execute("select text from events where session=? and kind='session_end'", (s,)).fetchone()["text"]
        msgs = [dict(r) for r in c.execute("select id,agent,text,meta from events where session=? and kind='message' order by id", (s,))]
        docs = [dict(r) for r in c.execute("select id,agent,text,meta from events where session=? and kind='doc' order by id", (s,))]
        rejected = c.execute("select count(*) from events where session=? and kind='doc_rejected'", (s,)).fetchone()[0]
        share = Counter(m["agent"] for m in msgs)
        info = dict(condition=meta["condition"], rep=meta["rep"], stop=endkind, messages=len(msgs), doc_versions=len(docs), rejected_edits=rejected,
                    doc_authors=[d["agent"] for d in docs], usd=round(end["usd"], 4), agreed_by=end["agreed"], roles=roles,
                    talk_share_by_agent={a: share.get(a, 0) for a in "ABCDEFGHI"}, max_talk_share=round(max(share.values()) / max(len(msgs), 1), 3))
        out["sessions"][s] = info
        final = docs[-1]["text"] if docs else ""
        (ROOT / "results" / "docs" / f"session{s}_{meta['condition']}_rep{meta['rep']}_final.md").write_text(final)
        info["final_doc_words"] = len(final.split())
        jobs_doc.append((s, final))
        order = list("XYZPQRSTU"); rng.shuffle(order); amap[s] = dict(zip("ABCDEFGHI", order))
        # role recognition: 12 substantive messages per agent (skip pure AGREE and document markers)
        for a in "ABCDEFGHI":
            own = [m["text"] for m in msgs if m["agent"] == a and not m["text"].startswith("[posted document") and len(m["text"]) > 60 and not re.fullmatch(r"\s*AGREE\s+v?\d+\s*", m["text"])]
            if len(own) >= 2:   # agents say only a handful of substantive things in a ~40-message session (amendment 2)
                jobs_role.append((s, a, own[:12]))
        for n, m in enumerate(msgs):
            if m["text"].startswith("[posted document"): continue
            ctx = "\n".join(f"Speaker {amap[s][x['agent']]}: {x['text'][:500]}" for x in msgs[max(0, n - 6):n])
            jobs_stance.append((s, m["id"], m["agent"], f"Previous messages of a team chat:\n{ctx or '(none)'}\n\nTARGET (Speaker {amap[s][m['agent']]}): {m['text'][:1200]}\n\n"
                                'Code the TARGET only. JSON only: {"stance": "challenge" | "agree" | "neutral"}. challenge = disputes, corrects or points out a flaw in an earlier message or the document; '
                                "agree = endorses without disputing (even if it adds); neutral = neither (proposal, question, opening)."))
    names = [r["role"] for r in ROLES]
    role_prompt = lambda msgs: ("Below are messages written by ONE member of a team that was designing a cloud platform. Using only the messages, say which of the nine Belbin team roles this person's way of "
                                "working fits best.\nRoles:\n" + "\n".join(f"- {n}: {DESC[n]}" for n in names) + "\n\nMESSAGES:\n" + "\n---\n".join(t[:900] for t in msgs) +
                                '\n\nJSON only: {"role": "<one of the nine names exactly>"}')
    doc_prompt = lambda t: ("Score a design document for a highly available GKE cluster platform against this checklist. For each item give 0 (absent), 1 (mentioned only generically) or 2 (specific: names the "
                            "mechanism and the setting or number). Score coverage and specificity only, not correctness.\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(CHECK)) +
                            '\n\nAlso list up to 8 claims about GKE or Google Cloud behaviour in the document that look factually wrong or overstated.\n\nDOCUMENT:\n' + (t or "(empty)")[:30000] +
                            '\n\nJSON only: {"scores": [12 integers], "doubtful_claims": ["..."]}')
    with ThreadPoolExecutor(6) as ex:
        role_res = list(ex.map(lambda j: (j, ask(role_prompt(j[2]))), jobs_role))
        stance_res = list(ex.map(lambda j: (j, ask(j[3])), jobs_stance))
        doc_res = list(ex.map(lambda j: (j, ask(doc_prompt(j[1]), 8000)), jobs_doc))
    # role recognisability
    rr = defaultdict(list)
    for (s, a, _), r in role_res:
        rr[s].append(dict(agent=a, assigned=out["sessions"][s]["roles"][a], guessed=(r or {}).get("role")))
    for s, rows in rr.items(): out["sessions"][s]["role_guesses"] = rows
    def acc(cond):
        rows = [(x, s) for s, v in rr.items() if out["sessions"][s]["condition"] == cond for x in v]
        return rows
    bel = acc("belbin"); hit = sum(1 for x, s in bel if x["guessed"] == x["assigned"])
    out["role_recognition_belbin"] = dict(correct=hit, n=len(bel), accuracy=round(hit / len(bel), 3) if bel else None, chance=round(1 / 9, 3),
                                          guess_distribution=dict(Counter(x["guessed"] for x, _ in bel)))
    ctl = acc("control")
    # for control there is no assigned role: report the guess distribution, and agreement with the role the letter holds in the matching BELBIN repetition
    match = 0
    for x, s in ctl:
        rep = out["sessions"][s]["rep"]
        ref = next((out["sessions"][b]["roles"] for b in out["sessions"] if out["sessions"][b]["condition"] == "belbin" and out["sessions"][b]["rep"] == rep), {})
        match += (x["guessed"] == ref.get(x["agent"]))
    out["role_recognition_control"] = dict(n=len(ctl), matches_letter_role_in_matching_belbin_rep=match, guess_distribution=dict(Counter(x["guessed"] for x, _ in ctl)))
    # stance
    st = defaultdict(list)
    for (s, i, a, _), r in stance_res: st[s].append((a, (r or {}).get("stance")))
    for s, v in st.items():
        n = len([1 for _, x in v if x]); out["sessions"][s]["stance"] = {k: round(sum(1 for _, x in v if x == k) / max(n, 1), 3) for k in ("challenge", "agree", "neutral")} | {"n": n}
    # checklist
    for (s, _), r in doc_res:
        sc = (r or {}).get("scores") or []
        out["sessions"][s]["checklist"] = dict(items=sc, total=sum(sc) if len(sc) == 12 else None, doubtful_claims=(r or {}).get("doubtful_claims", []))
    cond = defaultdict(list)
    for s, v in out["sessions"].items(): cond[v["condition"]].append(s)
    out["by_condition"] = {k: dict(sessions=v, checklist_totals=[out["sessions"][s]["checklist"]["total"] for s in v], messages=[out["sessions"][s]["messages"] for s in v],
                                   challenge_share=[out["sessions"][s]["stance"]["challenge"] for s in v], rejected_edits=[out["sessions"][s]["rejected_edits"] for s in v],
                                   stop=[out["sessions"][s]["stop"] for s in v]) for k, v in cond.items()}
    out["coder"] = CODER; out["coder_tokens"] = dict(tot); out["coder_cost_usd_list"] = round((tot["in"] * 0.1 + tot["out"] * 0.5) / 1e6, 4)
    (ROOT / "results" / "analysis.json").write_text(json.dumps(out, indent=1))
    ids = [(s, i, a) for (s, i, a, _), _ in stance_res]; rng.shuffle(ids)
    txt = {r["id"]: r["text"] for r in c.execute("select id,text from events where kind='message'")}
    cmap = {(s, i): (r or {}).get("stance") for (s, i, a, _), r in stance_res}
    with open(ROOT / "results" / "coded_sample_for_hand_check.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["session", "event_id", "speaker", "coder_stance", "text", "your_stance"])
        for s, i, a in ids[:40]: w.writerow([s, i, amap[s][a], cmap[(s, i)], txt[i][:600].replace("\n", " "), ""])
    print(json.dumps({k: v for k, v in out.items() if k != "sessions"}, indent=1))
    for s, v in out["sessions"].items(): print(s, {k: v[k] for k in ("condition", "rep", "stop", "messages", "doc_versions", "rejected_edits", "usd", "final_doc_words", "stance", "checklist")})


main()
