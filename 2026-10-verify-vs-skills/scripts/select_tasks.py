"""Applies the selection rule and the gate fixed in the README ("Tasks") to the calibration runs.

Each candidate scores its calibration passes in arm A (none, low effort) plus arm D (medium, medium effort), 0 to 4. The 20
lowest are kept; ties are broken by the D score, then by task id. Gate: at least 8 of the 20 kept tasks scored 0 or 1
of 2 for arm D. Writes results/calibration.md and, if the gate passes, regenerates the trial files for the kept tasks.

Usage: python3 -I select_tasks.py <calibration runs dir (low)> <calibration runs dir (medium)>
"""
import glob, json, os, subprocess, sys

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP, GATE = 20, 8
low, high = sys.argv[1], sys.argv[2]


def passes(runs, task, arm):
    out = []
    for f in sorted(glob.glob(os.path.join(runs, task, arm, "codex", "*", "run.json"))):
        d = json.load(open(f))
        sp = os.path.join(os.path.dirname(f), "verify-summary.json")
        out.append(d["status"] == "ok" and os.path.exists(sp) and json.load(open(sp))["pass"])
    return sum(out), len(out)


tasks = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(E, "tasks", "*", "prompt.md")))
rows = []
for t in tasks:
    a, na = passes(low, t, "none")
    d, nd = passes(high, t, "medium")
    rows.append((a + d, d, t, a, na, nd))
rows.sort()
chosen = sorted(r[2] for r in rows[:KEEP])
hard_high = sum(1 for r in rows[:KEEP] if r[1] <= 1)
gate = hard_high >= GATE
os.makedirs(os.path.join(E, "results"), exist_ok=True)
with open(os.path.join(E, "results", "calibration.md"), "w") as fh:
    fh.write("# Calibration (arms A and D, 2 runs per task)\n\nRule, fixed before calibration: keep the 20 tasks with the lowest "
             "A + D score, ties broken by the D score and then by task id. Gate: at least 8 kept tasks score 0 or 1 of 2 in D. "
             "These runs are not part of the results.\n\n| task | kind | A (low) | D (medium) | score | kept |\n| --- | --- | --- | --- | --- | --- |\n")
    for s, d, t, a, na, nd in sorted(rows, key=lambda r: r[2]):
        kind = "N" if os.path.exists(os.path.join(E, "tasks", t, "naive.patch")) else "R"
        fh.write(f"| {t} | {kind} | {a}/{na} | {d}/{nd} | {s} | {'yes' if t in chosen else 'no'} |\n")
    fh.write(f"\nKept tasks scoring 0 or 1 of 2 in D: {hard_high} (gate needs {GATE}): **{'passed' if gate else 'not passed'}**.\n")
print("chosen:", chosen, "| hard at high:", hard_high, "| gate:", "passed" if gate else "NOT passed")
if gate:
    subprocess.run([sys.executable, "-I", os.path.join(E, "scripts", "make_trial.py")] + chosen, check=True)
