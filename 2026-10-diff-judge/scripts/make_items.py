"""Selects the diffs to be judged (README, "Items"). Fixed before any judgement.

Source: every graded run of the four experiments that share TSK's 20 shopizer tasks and hidden tests (verify-vs-skills,
repo-skills, explicit-skills, test-skill), at commit e3908706. Ground truth: the run's verified pass (verify-summary.json
pass and status ok). Eligible tasks: at least 4 passing and 4 failing runs. For each eligible task, 4 failing and 4
passing runs are drawn with random.Random(1), in sorted order of run path. Dry-run items (for trying the prompt only,
never scored): 6 runs, 3 passing and 3 failing, from the ineligible tasks, drawn the same way.
Writes items/items.json and items/dryrun.json. Usage: python3 -I make_items.py
"""
import glob, json, os, random
HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE); X = os.path.dirname(N)
EXPS = ["2026-10-verify-vs-skills", "2026-10-repo-skills", "2026-10-explicit-skills", "2026-10-test-skill"]
runs = []
for exp in EXPS:
    for f in sorted(glob.glob(os.path.join(X, exp, "results/*/runs/*/*/*/*/run.json"))):
        rd = os.path.dirname(f); r = json.load(open(f)); s = json.load(open(os.path.join(rd, "verify-summary.json")))
        kind = "pass" if (s.get("pass") and r["status"] == "ok") else (
            "neighbour break" if s.get("keeps_broken") else "existing tests broken" if s.get("other_failures")
            else "hidden tests fail" if s.get("hidden_tests") == s.get("hidden_expected") else "build or grading failure")
        runs.append(dict(id=os.path.relpath(rd, X), task=r["question"], arm=r["arm"], passed=kind == "pass", kind=kind,
                         claim=(r.get("claim") or {}).get("result") if isinstance(r.get("claim"), dict) else None))
tasks = sorted({r["task"] for r in runs})
rng = random.Random(1)
items, dry_pool = [], []
for t in tasks:
    p = [r for r in runs if r["task"] == t and r["passed"]]; f = [r for r in runs if r["task"] == t and not r["passed"]]
    if len(p) >= 4 and len(f) >= 4:
        items += rng.sample(f, 4) + rng.sample(p, 4)
    else:
        dry_pool += p + f
dry = rng.sample([r for r in dry_pool if not r["passed"]], 3) + rng.sample([r for r in dry_pool if r["passed"]], 3)
json.dump(items, open(os.path.join(N, "items", "items.json"), "w"), indent=1)
json.dump(dry, open(os.path.join(N, "items", "dryrun.json"), "w"), indent=1)
from collections import Counter
print(len(items), "items from", len({i["task"] for i in items}), "tasks;", Counter(i["kind"] for i in items))
print("agent claimed 'passed' in", sum(i["claim"] == "passed" for i in items), "of", len(items), "| by source:", Counter(i["id"].split("/")[0] for i in items))
print("dry-run tasks:", sorted({d["task"] for d in dry}))
