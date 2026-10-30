"""Runs architectures x models x cases x repetitions and writes one JSON line per run to <out>/runs.jsonl.

Each run: a fresh Shop with the case's faults, the architecture's run(email, shop, llm), then grade.py. Resumable:
runs already in runs.jsonl are skipped. Runs go 8 at a time in threads, in a shuffled order (seed 1) so no
architecture or case always runs at the same time of day.
Each case runs in two wordings: "original" (cases.py, which I read while writing the plain-code rules) and
"paraphrased" (cases/paraphrased.json, rewritten by a model not under test; see paraphrase.py).
Accounts are "small" (1-3 orders) or "large" (40 older orders added to each; shop.history_orders).
Usage: python3 -I run.py <out> [--arms ...] [--histories small,large] [--models a,b] [--reps N] [--cases L1-01,...] [--wordings original,paraphrased]
"""
import argparse, json, os, random, sys, threading, time, traceback
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent, rules, single, workflow  # noqa: E402
from cases import CASES  # noqa: E402
from grade import grade  # noqa: E402
from llm import LLM  # noqa: E402
from shop import Shop  # noqa: E402

ARMS = {"rules": rules, "single": single, "workflow": workflow, "agent": agent}
MODELS = ["openai/gpt-6-luna", "qwen/qwen3.7-flash"]
LOCK = threading.Lock()
PARA = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cases",
                                   "paraphrased.json")))


def one(case, wording, history, arm, model, rep, out):
    shop = Shop(case["faults"], history=history == "large")
    llm = LLM(model) if arm != "rules" else None
    text = case if wording == "original" else PARA[case["id"]]
    email = {"sender": case["sender"], "subject": text["subject"], "body": text["body"]}
    t = time.time()
    try:
        reply, error = ARMS[arm].run(email, shop, llm), None
    except Exception:
        reply, error = "", traceback.format_exc(limit=3)
    g = grade(case, shop.actions, reply)
    if error:
        g["outcome"] = "crashed"
    rec = {"case": case["id"], "wording": wording, "history": history, "level": case["level"], "known": case["known"], "arm": arm,
           "model": model if arm != "rules" else "none", "rep": rep, "seconds": round(time.time() - t, 2),
           **g, "actions": shop.actions, "reply": reply, "tool_calls": shop.calls, "error": error,
           **(llm.usage() if llm else {"llm_calls": 0, "cost": 0.0})}
    with LOCK, open(os.path.join(out, "runs.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--cases", default="")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--wordings", default="original,paraphrased")
    ap.add_argument("--histories", default="small,large")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "runs.jsonl")
    done = set()
    if os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            done.add((r["case"], r.get("wording", "original"), r.get("history", "small"), r["arm"], r["model"], r["rep"]))
    cases = [c for c in CASES if not a.cases or c["id"] in a.cases.split(",")]
    jobs = []
    for arm in a.arms.split(","):
        for model in (["none"] if arm == "rules" else a.models.split(",")):
            for c in cases:
                for w in a.wordings.split(","):
                    for h in a.histories.split(","):
                        for rep in range(1, a.reps + 1):
                            if (c["id"], w, h, arm, model, rep) not in done:
                                jobs.append((c, w, h, arm, model, rep))
    random.Random(1).shuffle(jobs)
    print(f"{len(jobs)} runs to do", flush=True)
    cost = 0.0
    with ThreadPoolExecutor(a.workers) as ex:
        for i, rec in enumerate(ex.map(lambda j: one(*j, a.out), jobs), 1):
            cost += rec.get("cost", 0.0)
            if i % 25 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} done, ${cost:.3f}", flush=True)


if __name__ == "__main__":
    main()
