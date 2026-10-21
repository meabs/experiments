"""Applies the preregistered selection rule to the calibration runs: keep the 16 tasks with the lowest `none` pass
rate, ties broken by task id. Writes results/calibration.md and regenerates trial.toml for the chosen tasks.

Usage: python3 -I select_tasks.py <calibration runs dir>
"""
import glob, json, os, subprocess, sys

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = 16
runs = sys.argv[1]
sys.path.insert(0, os.path.join(E, "scripts"))
from make_trial import EXCLUDE  # noqa: E402
tasks = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(E, "tasks", "*", "prompt.md"))
               if os.path.basename(os.path.dirname(p)) not in EXCLUDE)
rows = []
for t in tasks:
    res = []
    for f in sorted(glob.glob(os.path.join(runs, t, "none", "codex", "*", "run.json"))):
        d = json.load(open(f))
        sp = os.path.join(os.path.dirname(f), "verify-summary.json")
        ok = d["status"] == "ok" and os.path.exists(sp) and json.load(open(sp))["pass"]
        res.append(ok)
    rows.append((sum(res), t, len(res)))
rows.sort()
chosen = sorted(t for _, t, _ in rows[:KEEP])
os.makedirs(os.path.join(E, "results"), exist_ok=True)
with open(os.path.join(E, "results", "calibration.md"), "w") as fh:
    fh.write("# Calibration (control only, low reasoning effort, 2 runs per task)\n\nRule, fixed before calibration: keep the 16 tasks with the "
             "lowest `none` pass rate, ties broken by task id. These runs are not part of the results.\n\n"
             "| task | passed | kept |\n| --- | --- | --- |\n")
    for p, t, n in sorted(rows, key=lambda r: r[1]):
        fh.write(f"| {t} | {p}/{n} | {'yes' if t in chosen else 'no'} |\n")
print("dropped:", [t for _, t, _ in rows[KEEP:]], "chosen:", len(chosen))
subprocess.run([sys.executable, "-I", os.path.join(E, "scripts", "make_trial.py")] + chosen, check=True)
