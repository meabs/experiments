"""Runs architectures x models x cases x wordings x account sizes x repetitions; one JSON line per run in
<out>/runs.jsonl. Resumable (finished runs are skipped); shuffled order (seed 1); threads.

Each run: a fresh need-an-agent Shop with the case's faults, the architecture's run(email, shop, llm), then grade.
Grading is need-an-agent's grade.py, with one change for emails with several requests: escalations are counted once
(two escalations in one run match one expected escalation), because a compound email can be escalated per request.
Usage: python3 -I run.py <out> [--arms ...] [--models a,b] [--reps N] [--cases L6-01,...] [--levels 6]
                                [--wordings original,paraphrased] [--histories small,large] [--workers N]
"""
import argparse, json, os, random, sys, threading, time, traceback
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402,F401
import agent, crew, statemachine  # noqa: E402
from crewcases import CASES  # noqa: E402
from grade import grade as na_grade  # noqa: E402
from llm import LLM  # noqa: E402
from shop import Shop  # noqa: E402

agent.MAX_STEPS = crew.MAX_STEPS        # the same step budget for the single agent and the whole crew
ARMS = {"statemachine": statemachine.run, "agent": agent.run, "crew_shared": crew.run_shared, "crew_note": crew.run_note}
MODELS = ["openai/gpt-6-luna", "qwen/qwen3.7-flash"]
LOCK = threading.Lock()
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARA = json.load(open(os.path.join(E, "cases", "paraphrased.json")))


def grade(case, actions, reply):
    once, seen = [], False
    for a in actions:
        if a["type"] == "escalate":
            if seen:
                continue
            seen = True
        once.append(a)
    g = na_grade(case, once, reply)
    g["escalations"] = sum(a["type"] == "escalate" for a in actions)
    return g


def one(case, wording, history, arm, model, rep, out):
    shop = Shop(case["faults"], history=history == "large")
    shop.handoffs = []
    llm = LLM(model)
    text = case if wording == "original" else PARA[case["id"]]
    email = {"sender": case["sender"], "subject": text["subject"], "body": text["body"]}
    t = time.time()
    try:
        reply, error = ARMS[arm](email, shop, llm), None
    except Exception:
        reply, error = "", traceback.format_exc(limit=3)
    g = grade(case, shop.actions, reply)
    if error:
        g["outcome"] = "crashed"
    rec = {"case": case["id"], "wording": wording, "history": history, "level": case["level"], "arm": arm,
           "model": model, "rep": rep, "seconds": round(time.time() - t, 2), **g, "actions": shop.actions,
           "reply": reply, "tool_calls": shop.calls, "handoffs": shop.handoffs, "error": error, **llm.usage()}
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
    ap.add_argument("--levels", default="")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--wordings", default="original,paraphrased")
    ap.add_argument("--histories", default="small,large")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "runs.jsonl")
    done = set()
    if os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            done.add((r["case"], r["wording"], r["history"], r["arm"], r["model"], r["rep"]))
    cases = [c for c in CASES if (not a.cases or c["id"] in a.cases.split(","))
             and (not a.levels or str(c["level"]) in a.levels.split(","))]
    jobs = [(c, w, h, arm, m, rep) for arm in a.arms.split(",") for m in a.models.split(",") for c in cases
            for w in a.wordings.split(",") for h in a.histories.split(",") for rep in range(1, a.reps + 1)
            if (c["id"], w, h, arm, m, rep) not in done]
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
