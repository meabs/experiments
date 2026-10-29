"""Regrades finished runs of one task with the current hidden test (amendment 2026-10-29, S08).
For each run: copies the starter repo, lays the arm's files over it (setup.sh), applies the agent's saved diff
(agent.diff), and grades it with grade.py. The original grade.json is kept once as grade.v1.json.
Usage: python3 -I regrade.py <out dir> <task> [starter repo]
"""
import glob, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grade  # noqa: E402

out, task = sys.argv[1], sys.argv[2]
starter = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/code/benchmark/sec-authz-work/accounts-service")
runs = sorted(glob.glob(os.path.join(out, "*", "runs", task, "*", "*", "*", "agent.diff")))
changed = 0
for diff in runs:
    r = os.path.dirname(diff)
    arm = r.split(os.sep)[-3]
    with tempfile.TemporaryDirectory() as tmp:
        ws = os.path.join(tmp, "ws")
        shutil.copytree(starter, ws, ignore=shutil.ignore_patterns(".git", "target"))
        env = dict(os.environ, TRIAL_QUESTION=task)
        subprocess.run(["bash", os.path.join(HERE, "setup.sh"), arm], cwd=ws, env=env, check=True)
        if os.path.getsize(diff):
            subprocess.run(["git", "apply", "--whitespace=nowarn", diff], cwd=ws, check=True)
        res = grade.grade(task, ws)
    old = os.path.join(r, "grade.json")
    v1 = os.path.join(r, "grade.v1.json")
    if not os.path.exists(v1):
        shutil.copy(old, v1)
    before = json.load(open(v1))["pass"]
    with open(old, "w") as f:
        json.dump(res, f, indent=1)
    changed += before != res["pass"]
    print(os.path.relpath(r, out), "v1", "pass" if before else "fail", "-> now", "pass" if res["pass"] else "fail",
          res["failed"][:3])
print(f"{len(runs)} runs regraded, {changed} changed")
