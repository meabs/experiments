"""Runs a batch, one run at a time (one GPU), model by model, tasks in shuffled order within each model (seed 1).

  python3 -I batch.py pilot      one run per model per task (40 runs)
  python3 -I batch.py main       3 runs per model per task (120 runs)
  python3 -I batch.py <batch> --models qwen3-coder:30b,gpt-oss:20b     only these models

$LC_WORK/<batch>/key.json maps each run ID to its cell; a run that already has grade.json is skipped, so a batch can
be resumed. Before each model's block the model is loaded with a short warm-up request, so loading time isn't counted
in the first run.
"""
import json, os, random, subprocess, sys, urllib.request

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(E, "scripts"))
from run import MODELS, MODELS_PILOT, TASKS  # noqa: E402

BASE = os.environ.get("LC_WORK", os.path.expanduser("~/code/benchmark/lc-work"))


def cells(batch):
    reps = 1 if batch == "pilot" else 3
    out, rng = [], random.Random(1)
    for m in (MODELS_PILOT if batch == "pilot" else MODELS):
        block = [(m, t, r) for r in range(1, reps + 1) for t in TASKS]
        rng.shuffle(block)
        out += block
    return out


def warm(model):
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", method="POST",
                                 data=json.dumps({"model": model, "prompt": "hi", "stream": False,
                                                  "options": {"num_predict": 1}}).encode())
    urllib.request.urlopen(req, timeout=900).read()


def main(batch, only=None):
    work = os.path.join(BASE, batch)
    os.makedirs(work, exist_ok=True)
    kp = os.path.join(work, "key.json")
    key = json.load(open(kp)) if os.path.exists(kp) else {}
    if not key:
        prefix = "p" if batch == "pilot" else "m"
        key = {f"{prefix}{i + 1:03d}": {"model": m, "task": t, "rep": r} for i, (m, t, r) in enumerate(cells(batch))}
        json.dump(key, open(kp, "w"), indent=1)
    env = {**os.environ, "LC_WORK": work}
    run_py = os.path.join(E, "scripts", "run.py")
    warmed = None
    for rid in sorted(key):
        c = key[rid]
        if only and c["model"] not in only:
            continue
        d = os.path.join(work, rid)
        if os.path.exists(os.path.join(d, "grade.json")):
            continue
        if os.path.exists(d):
            subprocess.run(["rm", "-rf", d], check=True)
        if warmed != c["model"]:
            warm(c["model"])
            warmed = c["model"]
        for args in (["new", rid, "--model", c["model"], "--task", c["task"]], ["go", rid], ["grade", rid]):
            p = subprocess.run([sys.executable, "-I", run_py] + args, env=env, capture_output=True, text=True)
            if args[0] != "new":
                print(p.stdout.strip() or p.stderr.strip()[-300:], flush=True)


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--models") + 1].split(",") if "--models" in sys.argv else None
    main(sys.argv[1], only)
