"""Runs a batch of cells, a few at a time, each as new + go + grade, under anonymous run IDs.

  python3 -I batch.py pilot      M under every condition and C under EXCL1, one run per ticket (20 runs)
  python3 -I batch.py main       C x {F0, EXCL, EXCL1} and M x {F0, EXCL, EXCL1, STALE}, 4 tickets, 4 runs each
                                 (112 runs), in shuffled order (seed 1)

$CG_WORK/<batch>/key.json maps each anonymous run ID to its cell; a run that already has grade.json is skipped, so a
batch can be resumed.
"""
import json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(E, "scripts"))
from run import TASKS, ARMS, FAULTS  # noqa: E402

BASE = os.environ.get("CG_WORK", os.path.expanduser("~/code/benchmark/cg-work"))
PARALLEL = 4


def cells(batch):
    if batch == "pilot":
        return [(t, "M", f, 1) for t in TASKS for f in FAULTS] + [(t, "C", "EXCL1", 1) for t in TASKS]
    return [(t, a, f, r) for r in (1, 2, 3, 4) for t in TASKS for a in ARMS for f in FAULTS
            if not (f == "STALE" and a != "M")]


def main(batch):
    work = os.path.join(BASE, batch)
    os.makedirs(work, exist_ok=True)
    kp = os.path.join(work, "key.json")
    key = json.load(open(kp)) if os.path.exists(kp) else {}
    if not key:
        cs = cells(batch)
        random.Random(1).shuffle(cs)
        prefix = "p" if batch == "pilot" else "m"
        key = {f"{prefix}{i + 1:03d}": {"task": t, "arm": a, "fault": f, "rep": r} for i, (t, a, f, r) in enumerate(cs)}
        json.dump(key, open(kp, "w"), indent=1)
    env = {**os.environ, "CG_WORK": work}
    run_py = os.path.join(E, "scripts", "run.py")

    def one(rid):
        c = key[rid]
        d = os.path.join(work, rid)
        if os.path.exists(os.path.join(d, "grade.json")):
            return
        if os.path.exists(d):
            subprocess.run(["rm", "-rf", d], check=True)   # an unfinished run starts again
        for args in (["new", rid, "--task", c["task"], "--arm", c["arm"], "--fault", c["fault"]], ["go", rid],
                     ["grade", rid]):
            p = subprocess.run([sys.executable, "-I", run_py] + args, env=env, capture_output=True, text=True)
            if args[0] != "new":
                print(p.stdout.strip() or p.stderr.strip()[-300:], flush=True)

    with ThreadPoolExecutor(PARALLEL) as ex:
        list(ex.map(one, sorted(key)))


if __name__ == "__main__":
    main(sys.argv[1])
