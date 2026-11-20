#!/usr/bin/env python3
"""PLC analysis (README sections 5 and 6); same coders and flaws as PLF and PLE, plus editor and checker measures and cross-run comparisons with PLE and PLF. Exploratory: five sessions per condition.
Counts of planted flaws found / fixed / remaining and false alarms come from blind coders (speakers anonymised, conditions not
named) that see the draft, the chat, the final document and flaws.json. Primary coder openai/gpt-6-luna; second coder
anthropic/claude-haiku-5.5 for agreement. Process numbers come from the event log.
usage: OPENROUTER_API_KEY=placeholder python3 -I scripts/analyse.py [events.sqlite] [out.json]"""
import csv, json, os, random, re, sqlite3, sys, time, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "results" / "events.sqlite")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results" / "analysis.json"
KEY = os.environ.get("OPENROUTER_API_KEY", "placeholder")
CODERS = {"primary": "openai/gpt-6-luna", "second": "anthropic/claude-haiku-5.5"}
PRICE = {"primary": (0.10, 0.50), "second": (0.10, 0.50)}
FLAWS = json.load(open(ROOT / "flaws.json"))
DRAFT = (ROOT / "arms" / "draft.md").read_text().strip()
tot = defaultdict(Counter)
rng = random.Random(1)


def ask(which, prompt, max_tokens=14000):
    body = json.dumps({"model": CODERS[which], "temperature": 0, "max_tokens": max_tokens, "reasoning": {"effort": "low"}, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body, {"Authorization": f"Bearer {KEY}", "content-type": "application/json"})
    for i in range(3):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300)); u = d["usage"]
            tot[which]["in"] += u.get("prompt_tokens", 0); tot[which]["out"] += u.get("completion_tokens", 0)
            raw = d["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", raw, re.S)
            return json.loads(m.group(0))
        except Exception as e:
            with open(OUT.parent / "coder_failures.log", "a") as f: f.write(f"{which} attempt {i}: {e!r}\n")
            time.sleep(2 * (i + 1))
    return None


def code_prompt(chat, final_doc):
    fl = "\n".join(f"{f['id']}. PLANTED: {f['planted']}\n   TRUTH: {f['truth']}\n   FIXED IF: {f['fixed_if']}" for f in FLAWS)
    return (
        "A team of nine reviewed a draft design document that contains planted flaws, then agreed a final version. Judge what happened.\n\n"
        f"THE PLANTED FLAWS:\n{fl}\n\nORIGINAL DRAFT:\n{DRAFT}\n\nTEAM CHAT (speakers anonymised, numbered):\n{chat}\n\nFINAL DOCUMENT (the version the team ended with):\n{final_doc}\n\n"
        f"For EACH of F1 to F{len(FLAWS)} give:\n- found: true if some speaker said in the chat that this statement of the draft was wrong or unsupported (correctly identifying the problem), else false;\n"
        "- first_message: the number of the first chat message that did so, or null;\n"
        '- status: "fixed" if the FINAL DOCUMENT meets the FIXED IF test; "still_present" if the flawed claim is still there; "changed_but_still_wrong" if it was changed but is still wrong;\n'
        "- evidence: a short quote (under 20 words) from the chat or the final document.\n"
        "Then list false alarms: distinct objections raised in the chat that criticise text in the draft that is actually correct, or edits in the final document that introduce a technical error "
        "(give message number or 'final', the claim, and why it is wrong). Do not list the planted flaws. List other_valid_issues: real defects in the original draft that were not planted and that a speaker correctly raised.\n"
        'JSON only: {"flaws": [{"id": "F1", "found": true, "first_message": 3, "status": "fixed", "evidence": "..."}, ...one item per flaw], '
        '"false_alarms": [{"where": "12", "claim": "...", "why": "..."}], "other_valid_issues": [{"where": "5", "issue": "..."}]}')


def main():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    sessions = [r["session"] for r in c.execute("select distinct session from events where session between 1 and 99 order by 1")]
    out = {"sessions": {}}
    jobs = []
    for s in sessions:
        st = c.execute("select text,meta from events where session=? and kind='session_start'", (s,)).fetchone()
        meta = json.loads(st["meta"])
        endrow = c.execute("select text,meta from events where session=? and kind='session_end'", (s,)).fetchone()
        if not endrow: continue
        end = json.loads(endrow["meta"])
        msgs = [dict(r) for r in c.execute("select id,agent,text from events where session=? and kind='message' order by id", (s,))]
        docs = [dict(r) for r in c.execute("select id,agent,text,meta from events where session=? and kind='doc' order by id", (s,))]
        ev = c.execute("select count(*) from events where session=? and kind='doc_rejected'", (s,)).fetchone()[0]
        order = list("XYZPQRSTU"); rng.shuffle(order); amap = dict(zip("ABCDEFGHI", order))
        chat = "\n".join(f"[{i+1}] Speaker {amap[m['agent']]}: {m['text'][:1500]}" for i, m in enumerate(msgs))
        final = docs[-1]["text"]
        agreed_at = None
        for i, m in enumerate(msgs):
            pass
        out["sessions"][s] = dict(condition=meta["condition"], rep=meta["rep"], doc_authors=[d["agent"] for d in docs[1:]], checker_messages=sum(1 for m in msgs if m["agent"] == "C"), editor_messages=sum(1 for m in msgs if m["agent"] == "E"), stop=endrow["text"], messages=len(msgs), doc_versions=len(docs), edits_accepted=len(docs) - 1,
                                  rejected_edits=ev, agreed_version=end["doc_version"], approved_v1_straight_away=(endrow["text"] == "agreed" and end["doc_version"] == 1),
                                  usd=round(end["usd"], 4), final_doc_words=len(final.split()), roles={})
        jobs.append((s, chat, final))
        (ROOT / "results" / "docs").mkdir(parents=True, exist_ok=True)
        (ROOT / "results" / "docs" / f"session{s:02d}_{meta['condition']}_rep{meta['rep']}_final.md").write_text(final)
    with ThreadPoolExecutor(6) as ex:
        res = {w: list(ex.map(lambda j: (j[0], ask(w, code_prompt(j[1], j[2]))), jobs)) for w in CODERS}
    for w in CODERS:
        for s, r in res[w]:
            fl = {f["id"]: f for f in ((r or {}).get("flaws") or [])}
            rows = []
            for f in FLAWS:
                x = fl.get(f["id"], {})
                rows.append(dict(id=f["id"], found=bool(x.get("found")), first_message=x.get("first_message"), status=x.get("status") or "missing", evidence=x.get("evidence", "")))
            found = sum(r_["found"] for r_ in rows); fixed = sum(r_["status"] == "fixed" for r_ in rows)
            gap = sum(1 for r_ in rows if r_["found"] and r_["status"] != "fixed")
            out["sessions"][s][w] = dict(flaws=rows, found=found, fixed=fixed, remaining=len(FLAWS) - fixed, found_not_fixed=gap,
                                         false_alarms=len((r or {}).get("false_alarms") or []), other_valid=len((r or {}).get("other_valid_issues") or []),
                                         false_alarm_list=(r or {}).get("false_alarms") or [], other_valid_list=(r or {}).get("other_valid_issues") or [], ok=r is not None)
    # agreement between coders (per flaw per session)
    agree = {"found": [0, 0], "fixed": [0, 0]}
    for s, v in out["sessions"].items():
        if "primary" not in v or "second" not in v: continue
        for a, b in zip(v["primary"]["flaws"], v["second"]["flaws"]):
            agree["found"][1] += 1; agree["found"][0] += a["found"] == b["found"]
            agree["fixed"][1] += 1; agree["fixed"][0] += (a["status"] == "fixed") == (b["status"] == "fixed")
    out["coder_agreement"] = {k: dict(agree=v[0], n=v[1], share=round(v[0] / max(v[1], 1), 3)) for k, v in agree.items()}
    # by condition
    byc = defaultdict(list)
    for s, v in out["sessions"].items(): byc[v["condition"]].append(s)
    def stats(ss, which, key):
        x = [out["sessions"][s][which][key] for s in ss if which in out["sessions"][s]]
        return dict(values=x, mean=round(sum(x) / len(x), 2) if x else None, min=min(x) if x else None, max=max(x) if x else None)
    out["by_condition"] = {}
    for cnd, ss in byc.items():
        d = {"sessions": ss}
        for which in CODERS:
            d[which] = {k: stats(ss, which, k) for k in ("remaining", "found", "fixed", "found_not_fixed", "false_alarms", "other_valid")}
        d["process"] = {k: [out["sessions"][s][k] for s in ss] for k in ("messages", "doc_versions", "edits_accepted", "rejected_edits", "approved_v1_straight_away", "usd")}
        out["by_condition"][cnd] = d
    # exploratory: difference in mean remaining flaws vs NONE (primary coder), bootstrap 95% interval, 10,000 resamples, seed 1
    brng = random.Random(1)
    def boot(a, b):
        diffs = []
        for _ in range(10000):
            ra = [brng.choice(a) for _ in a]; rb = [brng.choice(b) for _ in b]
            diffs.append(sum(ra) / len(ra) - sum(rb) / len(rb))
        diffs.sort(); return [round(diffs[250], 2), round(diffs[9749], 2)]
    out["vs_none_remaining_primary"] = {}
    if "none" in byc:
        base = [out["sessions"][s]["primary"]["remaining"] for s in byc["none"] if "primary" in out["sessions"][s]]
        for cnd, ss in byc.items():
            if cnd == "none": continue
            x = [out["sessions"][s]["primary"]["remaining"] for s in ss if "primary" in out["sessions"][s]]
            if x and base: out["vs_none_remaining_primary"][cnd] = dict(mean_difference=round(sum(x) / len(x) - sum(base) / len(base), 2), interval_95=boot(x, base))
    # editor measures
    allauth = [x for v in out["sessions"].values() for x in v["doc_authors"]]
    out["editor"] = dict(accepted_edits=len(allauth), by_editor=sum(1 for x in allauth if x == "E"), share=round(sum(1 for x in allauth if x == "E") / max(len(allauth), 1), 3),
                         sessions_with_no_accepted_edit=[s for s, v in out["sessions"].items() if not v["doc_authors"]])
    out["no_agreement_sessions"] = [s for s, v in out["sessions"].items() if v["stop"] != "agreed"]
    # cross-run comparison with PLF (same draft, flaws, coders and prompts, but no designated editor; run earlier the same day)
    for key, folder in (("vs_ple", "2026-11-planted-flaws-editor"), ("vs_plf", "2026-11-planted-flaws")):
      plf_path = ROOT.parent / folder / "results" / "analysis.json"
      if plf_path.exists():
        plf = json.load(open(plf_path))
        cmp = {}
        for cnd, ss in byc.items():
            x = [out["sessions"][s]["primary"]["remaining"] for s in ss if "primary" in out["sessions"][s]]
            y = [v["primary"]["remaining"] for v in plf["sessions"].values() if v["condition"] == cnd]
            if x and y:
                brng2 = random.Random(1); diffs = []
                for _ in range(10000):
                    ra = [brng2.choice(x) for _ in x]; rb = [brng2.choice(y) for _ in y]; diffs.append(sum(ra) / len(ra) - sum(rb) / len(rb))
                diffs.sort()
                cmp[cnd] = dict(editor_mean=round(sum(x) / len(x), 2), plf_mean=round(sum(y) / len(y), 2), editor_values=x, plf_values=y,
                                mean_difference=round(sum(x) / len(x) - sum(y) / len(y), 2), interval_95=[round(diffs[250], 2), round(diffs[9749], 2)])
        allx = [v["primary"]["remaining"] for v in out["sessions"].values() if "primary" in v]; ally = [v["primary"]["remaining"] for v in plf["sessions"].values()]
        cmp["all_teams"] = dict(editor_mean=round(sum(allx) / len(allx), 2), plf_mean=round(sum(ally) / len(ally), 2))
        cmp["no_agreement"] = dict(editor=len(out["no_agreement_sessions"]), plf=sum(1 for v in plf["sessions"].values() if v["stop"] != "agreed"), n_each=20)
        out[key] = cmp
    out["coders"] = CODERS
    out["coder_cost_usd_list"] = {w: round((tot[w]["in"] * PRICE[w][0] + tot[w]["out"] * PRICE[w][1]) / 1e6, 4) for w in CODERS}
    OUT.write_text(json.dumps(out, indent=1))
    # hand-check sample: flaw-by-flaw verdicts of 12 randomly chosen sessions
    pick = rng.sample(sorted(out["sessions"]), min(12, len(out["sessions"])))
    with open(OUT.parent / "coded_sample_for_hand_check.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["session", "flaw", "coder_found", "coder_first_message", "coder_status", "evidence", "your_found", "your_status"])
        for s in sorted(pick):
            for r_ in out["sessions"][s]["primary"]["flaws"]: w.writerow([s, r_["id"], r_["found"], r_["first_message"], r_["status"], r_["evidence"][:300], "", ""])
    print(json.dumps({k: v for k, v in out.items() if k not in ("sessions", "by_condition")}, indent=1))
    for cnd, d in out["by_condition"].items(): print(cnd, "remaining", d["primary"]["remaining"], "found", d["primary"]["found"]["values"], "false", d["primary"]["false_alarms"]["values"], d["process"]["messages"])
    for s, v in out["sessions"].items(): print(s, v["condition"], v["stop"], v["messages"], "found/fixed/remaining/fa", v["primary"]["found"], v["primary"]["fixed"], v["primary"]["remaining"], v["primary"]["false_alarms"], "| second", v["second"]["found"], v["second"]["fixed"], v["second"]["remaining"], v["second"]["false_alarms"])


main()
