"""Creates and runs the main run: 70 runs in a shuffled order (seed 1), 4 at a time, resumable.

Usage: python3 -I batch.py      ($VH_WORK/main; key.json maps anonymous run IDs to arm, model and repetition)
"""
import json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(os.environ.get("VH_WORK", os.path.expanduser("~/code/benchmark/vh-work")), "main")
PLAN = [(a, "luna") for a in ("A", "A2", "B", "C", "D")] + [("B", "qwen"), ("C", "qwen")]
REPS = 10


def main():
    os.makedirs(W, exist_ok=True)
    kp = os.path.join(W, "key.json")
    if not os.path.exists(kp):
        cells = [(a, m, r) for a, m in PLAN for r in range(1, REPS + 1)]
        random.Random(1).shuffle(cells)
        json.dump({f"r{i + 1:03d}": {"arm": a, "model": m, "rep": r} for i, (a, m, r) in enumerate(cells)},
                  open(kp, "w"), indent=1)
    key = json.load(open(kp))
    env = {**os.environ, "VH_WORK": W}
    todo = []
    for run, k in key.items():
        d = os.path.join(W, run)
        if not os.path.exists(d):
            subprocess.run([sys.executable, "-I", os.path.join(HERE, "run.py"), "new", run, "--arm", k["arm"],
                            "--model", k["model"]], env=env, check=True, capture_output=True)
        if "seconds" not in json.load(open(os.path.join(d, "meta.json"))):
            todo.append(run)

    def go(run):
        p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "run.py"), "go", run], env=env,
                           capture_output=True, text=True)
        print((p.stdout.strip().splitlines() or [f"{run} no output: {p.stderr[-300:]}"])[-1], flush=True)

    print(len(todo), "to run", flush=True)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(go, todo))


if __name__ == "__main__":
    main()
