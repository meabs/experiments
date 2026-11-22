#!/usr/bin/env python3
"""Per-arm, per-stage summaries from results/main. Re-grades every saved store with the current grader (kb-stages/stageN.json, exported from each arm's git history; the history itself is in kb-git.tar.gz)."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w

root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/main")
rows, per = [], {}
for f in sorted(root.glob("*/result.json")):
    r = json.loads(f.read_text()); arm, seed = r["arm"], r["seed"]; P = w.params(seed); folder = f.parent
    for st in r["stages"]:
        s = st["stage"]
        claims = json.loads((folder / "kb-stages" / f"stage{s}.json").read_text())
        g = w.grade_kb(P, claims, s)
        rows.append(dict(arm=arm, seed=seed, stage=s, score=round(st["score"], 3), attempts=st.get("attempts", 1), worker_calls=st["worker_calls"], gaps=st["gaps"],
                         curator_calls=st.get("curator_calls", 0), curator_rejected=st.get("curator_rejected", 0), **{k: int(v) for k, v in g.items()}))
fields = list(rows[0])
with open(root / "runs.csv", "w", newline="") as fh:
    wr = csv.DictWriter(fh, fields); wr.writeheader(); wr.writerows(rows)
out = {}
for arm in "ABCD":
    out[arm] = {}
    for s in w.STAGES:
        sel = [x for x in rows if x["arm"] == arm and x["stage"] == s]
        if not sel: continue
        n = len(sel); m = lambda k: round(sum(x[k] for x in sel) / n, 3)
        out[arm][s] = dict(n=n, score=m("score"), scores=[x["score"] for x in sel], claims=m("claims"), supported=m("supported"), other=m("other"), contamination=sum(x["contamination"] for x in sel),
                           source_ok=m("source_ok"), has_review=sum(x["has_review"] for x in sel), has_referral=sum(x["has_referral"] for x in sel), has_v2=sum(x["has_v2"] for x in sel),
                           curator_rejected=sum(x["curator_rejected"] for x in sel), worker_calls=m("worker_calls"), curator_calls=m("curator_calls"))
(root / "analysis.json").write_text(json.dumps(out, indent=1))
for arm in out:
    print(arm, {s: (v["score"], v["claims"], v["contamination"], v["has_referral"], v["has_review"], v["has_v2"]) for s, v in out[arm].items()})
