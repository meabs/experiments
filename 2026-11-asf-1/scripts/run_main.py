"""Runs the main trial: 4 repeats; within each repeat the 24 (ticket, arm) runs in a random order (seed 1), one at a
time. The schedule is written to results/main/schedule.json before the first run.

- Arm A: trialrig on a trial file holding just that ticket with reps = this repeat, so the rig runs only the missing
  repeat (earlier repeats are already done and skipped).
- Arms B and C: run_bc.py main TICKET:ARM:REP.

Resumable: a run whose result already exists is skipped. Usage: python3 -I run_main.py [--dry-run]
"""
import json
import os
import random
import subprocess
import sys

X = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(X, "scripts"))
from make_trial_a import TASKS  # noqa: E402

OUT = os.path.join(X, "results", "main")
RIG = os.path.expanduser("~/code/benchmark/AgentTrialRig")
REPS = 4
SEED = 1


def schedule():
    rng = random.Random(SEED)
    plan = []
    for rep in range(1, REPS + 1):
        block = [(t, a) for t in TASKS for a in "ABC"]
        rng.shuffle(block)
        plan += [{"ticket": t, "arm": a, "rep": rep} for t, a in block]
    return plan


def done(r):
    if r["arm"] == "A":
        return os.path.exists(os.path.join(OUT, "A", "runs", r["ticket"], "A", "codex", str(r["rep"]), "run.json"))
    f = os.path.join(OUT, "bc-runs.jsonl")
    return os.path.exists(f) and any(
        (j["ticket"], j["arm"], j["rep"]) == (r["ticket"], r["arm"], r["rep"]) for j in map(json.loads, open(f)))


def run(r):
    if r["arm"] == "A":
        subprocess.run(["python3", "-I", f"{X}/scripts/make_trial_a.py", "--main", "--tasks", r["ticket"],
                        "--reps", str(r["rep"])], check=True)
        with open(os.path.join(X, "results-main-A.log"), "a") as log:
            subprocess.run(["uv", "run", "trialrig", "run", f"{X}/trial-main-A.local.toml", "--agent", "codex",
                            "--out", os.path.join(OUT, "A")], cwd=RIG, stdout=log, stderr=subprocess.STDOUT, check=True)
    else:
        subprocess.run(["python3", "-I", f"{X}/scripts/run_bc.py", "main", f"{r['ticket']}:{r['arm']}:{r['rep']}"],
                       check=True)


def main():
    plan = schedule()
    f = os.path.join(OUT, "schedule.json")
    if "--dry-run" in sys.argv:
        for i, r in enumerate(plan, 1):
            print(f"[{i}/{len(plan)}] {r['ticket']}/{r['arm']}/{r['rep']}")
        return
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(f):
        assert json.load(open(f)) == plan, "schedule.json differs from the seeded schedule"
    else:
        json.dump(plan, open(f, "w"), indent=1)
    for i, r in enumerate(plan, 1):
        tag = f"[{i}/{len(plan)}] {r['ticket']}/{r['arm']}/{r['rep']}"
        if done(r):
            print(tag, "done already", flush=True)
            continue
        print(tag, "running", flush=True)
        run(r)


if __name__ == "__main__":
    main()
