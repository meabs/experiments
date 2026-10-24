"""Executes the experiment (README, "Procedure"): every scenario x condition x seed, in one shuffled order.

Conditions: clean, falsified, injection, combined (no verify tool); falsified_v, injection_v, combined_v (verify tool).
Seeds 1, 2, 3 (Ollama options.seed). Order: random.Random(2026).shuffle of all runs.
Writes <out>/runs.jsonl (one line per run, appended; done runs are skipped, so a run can resume) and
<out>/environment.json (Ollama version, model fingerprint and parameters, prompts, tool definitions, dataset hashes).
Usage: python3 -I src/run.py <out dir> [--pilot S01,S22,...] [--seeds 1] [--only <scenario>/<condition>/<seed>]
"""
import hashlib, json, os, platform, random, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import agent  # noqa: E402

CONDITIONS = {"clean": ("clean", False), "falsified": ("falsified", False), "injection": ("injection", False),
              "combined": ("combined", False), "falsified_v": ("falsified", True), "injection_v": ("injection", True),
              "combined_v": ("combined", True)}
SEEDS = (1, 2, 3)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def get(path, body=None):
    req = urllib.request.Request("http://localhost:11434" + path, json.dumps(body).encode() if body else None,
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def environment(S):
    show = get("/api/show", {"model": agent.MODEL})
    tags = [m for m in get("/api/tags")["models"] if m["name"] == agent.MODEL]
    try:
        env = subprocess.run(["systemctl", "show", "ollama", "-p", "Environment"], capture_output=True, text=True).stdout.strip()
    except OSError:
        env = None
    return dict(ollama_version=get("/api/version")["version"], model=agent.MODEL, model_digest=tags[0]["digest"] if tags else None,
                model_details=show.get("details"), model_parameters=show.get("parameters"), ollama_environment=env,
                think=True, num_predict=8000, max_rounds=agent.MAX_ROUNDS, seeds=SEEDS, conditions=CONDITIONS,
                system_prompt=agent.SYSTEM, final_nudge=agent.FINAL_NUDGE, schema=agent.SCHEMA,
                tool_definitions={"without_verify": agent.tools(["<sources of the alert>"], False),
                                  "with_verify": agent.tools(["<sources of the alert>"], True)},
                dataset={f: sha(os.path.join(ROOT, f)) for f in ("scenarios/scenarios.json", "manipulations/variants.json")},
                python=platform.python_version(), platform=platform.platform(), started=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                scenarios=len(S))


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    S = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "scenarios", "scenarios.json")))}
    V = json.load(open(os.path.join(ROOT, "manipulations", "variants.json")))
    ids = sorted(S)
    if "--pilot" in sys.argv:
        ids = sys.argv[sys.argv.index("--pilot") + 1].split(",")
    seeds = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")] if "--seeds" in sys.argv else SEEDS
    plan = [(i, c, s) for i in ids for c in CONDITIONS for s in seeds]
    random.Random(2026).shuffle(plan)
    if "--only" in sys.argv:
        i, c, s = sys.argv[sys.argv.index("--only") + 1].split("/")
        plan = [(i, c, int(s))]
    ef = os.path.join(out, "environment.json")
    if not os.path.exists(ef):
        json.dump(environment(S), open(ef, "w"), indent=1)
    rf = os.path.join(out, "runs.jsonl")
    done = set()
    if os.path.exists(rf):
        done = {(r["scenario"], r["condition"], r["seed"]) for r in map(json.loads, open(rf))}
    for n, (i, c, s) in enumerate(plan):
        if (i, c, s) in done and "--only" not in sys.argv:
            continue
        variant, use_verify = CONDITIONS[c]
        t = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        r = agent.run(S[i], V[i][variant], use_verify, s)
        rec = dict(scenario=i, condition=c, seed=s, variant=variant, verify_available=use_verify, order=n, started=t, **r)
        with open(rf if "--only" not in sys.argv else os.path.join(out, "replay.jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
        fin = r["final"] or {}
        print(f"{n + 1}/{len(plan)} {i} {c} s{s}: {fin.get('decision')} {fin.get('proposed_action')} "
              f"actions={[x['name'] for x in r['tool_calls'] if x['name'] in agent.ACTIONS]} {r['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
