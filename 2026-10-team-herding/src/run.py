"""Runs the experiment (README, "Procedure"). One unit = one case x one repeat; its stages run in order:

  solo       3 independent Luna agents (members 1-3)             -> arms A (member 1) and B (majority of 1-3)
  revise     each member again, shown its own and the other two  -> arm C (majority of the 3 revised)
             assessments
  recheck    1 Luna agent, then 3 resumed passes as a sceptical   -> arm E (token-matched single agent)
             second, third and fourth analyst
  sol_review Sol, shown the 3 revised assessments                 -> arm F
  sol_solo   Sol on its own                                       -> arm G

Units run 3 at a time, in one order shuffled with random.Random(2026). Every agent call is appended to
<out>/calls.jsonl (done calls are skipped, so a run can resume). Work folders and agent homes go under <out>/work and
<out>/homes; the homes hold the login and are never exported.
Usage: python3 -I src/run.py <out dir> [--cases S13-falsified,...] [--reps 2] [--parallel 3]
"""
import json, os, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import agent  # noqa: E402

LUNA, SOL = "gpt-5.6-luna", "gpt-5.6-sol"
LOCK = threading.Lock()


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
    C = {c["case"]: c for c in json.load(open(os.path.join(ROOT, "cases.json")))["cases"]}
    ids = arg("--cases", ",".join(sorted(C))).split(",")
    reps = int(arg("--reps", "2"))
    units = [(i, k) for i in ids for k in range(1, reps + 1)]
    random.Random(2026).shuffle(units)
    cf = os.path.join(out, "calls.jsonl")
    done = {}
    if os.path.exists(cf):
        for r in map(json.loads, open(cf)):
            done[(r["case"], r["rep"], r["stage"], r["member"])] = r
    env = os.path.join(out, "environment.json")
    if not os.path.exists(env):
        json.dump(dict(models={"luna": LUNA, "sol": SOL}, effort=agent.EFFORT, timeout=agent.TIMEOUT, reps=reps, cases=ids,
                       task=agent.TASK, schema=agent.SCHEMA, prompts=dict(solo=agent.SOLO, revise=agent.REVISE,
                       review=agent.REVIEW, recheck=agent.RECHECK), started=time.strftime("%Y-%m-%dT%H:%M:%S%z")),
                  open(env, "w"), indent=1)

    def do(case, k, stage, member, model, prompt, resume_of=None):
        key = (case["case"], k, stage, member)
        if key in done:
            return done[key]
        name = f"{case['case']}-r{k}-{stage}-{member}"
        work, home = os.path.join(out, "work", name), os.path.join(out, "homes", name)
        if resume_of:  # continue the same session, in the same work folder and home
            work, home = resume_of["_work"], resume_of["_home"]
        else:
            agent.make_work(work, case)
        r = agent.call(work, home, model, prompt, resume=resume_of["thread"] if resume_of else None)
        rec = dict(case=case["case"], scenario=case["scenario"], variant=case["variant"], rep=k, stage=stage, member=member,
                   started=time.strftime("%Y-%m-%dT%H:%M:%S%z"), actions=agent.actions(work), **r)
        with LOCK:
            open(cf, "a").write(json.dumps(rec) + "\n")
            done[key] = rec
            f = r["final"] or {}
            u = r["usage"]
            print(f"{name}: {f.get('decision')} {f.get('uncertainty')} manip={f.get('suspected_manipulation')} "
                  f"rc={r['returncode']} {r['seconds']}s in={u['input_tokens']} out={u['output_tokens']}", flush=True)
        rec["_work"], rec["_home"] = work, home
        return rec

    def unit(u):
        i, k = u
        case = C[i]
        solo = [do(case, k, "solo", m, LUNA, agent.SOLO) for m in (1, 2, 3)]
        a = [s["final"] for s in solo]
        [do(case, k, "revise", m, LUNA, agent.REVISE.format(own=agent.show(a[m - 1]),
                                                            p1=agent.show(a[m % 3]), p2=agent.show(a[(m + 1) % 3])))
         for m in (1, 2, 3)]
        rev = [done[(i, k, "revise", m)]["final"] for m in (1, 2, 3)]
        prev = do(case, k, "recheck", 1, LUNA, agent.SOLO)
        prev.setdefault("_work", os.path.join(out, "work", f"{i}-r{k}-recheck-1"))
        prev.setdefault("_home", os.path.join(out, "homes", f"{i}-r{k}-recheck-1"))
        for m, nth in ((2, "second"), (3, "third"), (4, "fourth")):
            if not prev.get("thread"):
                break
            r = do(case, k, "recheck", m, LUNA, agent.RECHECK.format(nth=nth), resume_of=prev)
            r.setdefault("_work", prev["_work"]); r.setdefault("_home", prev["_home"])
            r["thread"] = r.get("thread") or prev["thread"]
            prev = r
        do(case, k, "sol_review", 1, SOL, agent.REVIEW.format(a1=agent.show(rev[0]), a2=agent.show(rev[1]), a3=agent.show(rev[2])))
        do(case, k, "sol_solo", 1, SOL, agent.SOLO)

    with ThreadPoolExecutor(int(arg("--parallel", "3"))) as ex:
        for f in [ex.submit(unit, u) for u in units]:
            f.result()
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
