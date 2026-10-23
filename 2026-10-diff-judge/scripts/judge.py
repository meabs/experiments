"""Runs the judgements (README, "Arms" and "Procedure"). Each judgement is one `codex exec` call, read-only sandbox, in an
empty folder inside bubblewrap (setup/codex-bwrap.sh of 2026-10-test-skill-local), so the judge sees only the prompt.

  model local : qwen3.8:27b via Ollama (the local profile)        model hosted : gpt-5.6-luna (CODEX_PROFILE=hosted)
  arms        : diff (task + diff), claim (+ the agent's own final report), hedge (+ a fixed doubtful report)

Order: every (item, arm) pair in one order shuffled with random.Random(1); the same order for both models. A judgement
already on disk is skipped, so the script resumes after an interruption. Writes <out>/<model>/<arm>/<item key>/:
judgement.json (verdict, confidence, seconds, usage, tool calls), raw.out (Codex events), raw.err.
Usage: python3 -I judge.py <out dir> <local|hosted> [items.json] [--arms diff,claim,hedge] [--limit n] [--retest]
  --retest judges the first 24 items of the shuffled order again, arm diff only, into <out>/<model>-retest/.
"""
import argparse, json, os, random, re, subprocess, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE); X = os.path.dirname(N)
WRAP = os.path.expanduser("~/code/benchmark/local-setup/codex-bwrap.sh")
MODEL = {"local": "qwen3.8:27b", "hosted": "gpt-5.6-luna"}
TOML = {e: os.path.join(X, e, "trial.toml") for e in
        ["2026-10-verify-vs-skills", "2026-10-repo-skills", "2026-10-explicit-skills", "2026-10-test-skill"]}
TIMEOUT = 600

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("model", choices=MODEL); ap.add_argument("items", nargs="?", default=os.path.join(N, "items", "items.json"))
ap.add_argument("--arms", default="diff,claim,hedge"); ap.add_argument("--limit", type=int); ap.add_argument("--retest", action="store_true")
a = ap.parse_args()

import tomllib  # noqa: E402
TASKS = {}
for exp, p in TOML.items():
    TASKS[exp] = {q["id"]: q["prompt"] for q in tomllib.load(open(p, "rb"))["questions"]}
T = {k: open(os.path.join(N, "arms", f)).read() for k, f in
     [("prompt", "judge-prompt.md"), ("claim", "report-claim.md"), ("hedge", "report-hedge.md")]}
REPLY = re.compile(r"\n*When you have finished, reply with one short paragraph saying what you changed\.\s*$")


def prompt(item, arm):
    exp = item["id"].split("/")[0]
    rd = os.path.join(X, item["id"])
    task = REPLY.sub("", TASKS[exp][item["task"]]).strip()
    diff = open(os.path.join(rd, "agent.diff")).read().strip()
    rep = ""
    if arm == "claim":
        rep = T["claim"].replace("{answer}", (json.load(open(os.path.join(rd, "run.json"))).get("answer") or "").strip())
    elif arm == "hedge":
        rep = T["hedge"]
    return T["prompt"].replace("{task}", task).replace("{diff}", diff).replace("{report}", rep)


def parse(text):
    msg = ""
    usage, tools = {}, 0
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        it = e.get("item") or {}
        if e.get("type") == "item.completed" and it.get("type") == "agent_message":
            msg = it.get("text", "")
        if e.get("type") == "item.completed" and it.get("type") == "command_execution":
            tools += 1
        if e.get("type") == "turn.completed":
            usage = e.get("usage") or {}
    v = re.findall(r"VERDICT:\s*\**\s*(PASS|FAIL)", msg, re.I)
    c = re.findall(r"CONFIDENCE:\s*\**\s*(\d{1,3})", msg, re.I)
    return (v[-1].upper() if v else None), (min(100, int(c[-1])) if c else None), usage, tools, msg


items = json.load(open(a.items))
pairs = [(i, arm) for i in range(len(items)) for arm in a.arms.split(",")]
random.Random(1).shuffle(pairs)
if a.retest:
    seen, pairs = [], []
    order = [(i, arm) for i in range(len(items)) for arm in ["diff", "claim", "hedge"]]
    random.Random(1).shuffle(order)
    for i, arm in order:
        if arm == "diff" and i not in seen and len(seen) < 24:
            seen.append(i); pairs.append((i, "diff"))
if a.limit:
    pairs = pairs[:a.limit]
mdir = os.path.join(os.path.abspath(a.out), a.model + ("-retest" if a.retest else ""))
done = 0
for n, (i, arm) in enumerate(pairs, 1):
    item = items[i]
    key = re.sub(r"[^A-Za-z0-9]+", "_", item["id"]).strip("_")
    d = os.path.join(mdir, arm, key)
    if os.path.exists(os.path.join(d, "judgement.json")):
        continue
    work = os.path.join(mdir, "work", f"{arm}_{key}")
    os.makedirs(work, exist_ok=True); os.makedirs(d, exist_ok=True)
    env = dict(os.environ, TRIAL_OUT=mdir, TRIAL_ID=f"{arm}_{key}".lower())
    if a.model == "hosted":
        env["CODEX_PROFILE"] = "hosted"
    cmd = ["bash", WRAP, "exec", "-s", "read-only", "--skip-git-repo-check", "--json", "--model", MODEL[a.model],
           "-c", 'model_reasoning_effort="low"', prompt(item, arm)]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds"); t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
        out, err, rc, timed_out = r.stdout, r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as e:
        out, err, rc, timed_out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "", None, True
    secs = round(time.monotonic() - t0, 1)
    verdict, conf, usage, tools, msg = parse(out)
    open(os.path.join(d, "raw.out"), "w").write(out); open(os.path.join(d, "raw.err"), "w").write(err or "")
    rec = dict(item=item["id"], task=item["task"], truth="PASS" if item["passed"] else "FAIL", kind=item["kind"],
               agent_claim=item["claim"], arm=arm, model=MODEL[a.model], verdict=verdict, confidence=conf,
               correct=(verdict == ("PASS" if item["passed"] else "FAIL")) if verdict else None, seconds=secs,
               started=started, exit_code=rc, timed_out=timed_out, usage=usage, tool_calls=tools,
               diff_bytes=os.path.getsize(os.path.join(X, item["id"], "agent.diff")), final_message=msg)
    json.dump(rec, open(os.path.join(d, "judgement.json"), "w"), indent=1)
    done += 1
    print(f"[{n}/{len(pairs)}] {a.model} {arm} {item['task']} truth={rec['truth']} verdict={verdict} conf={conf} {secs}s", flush=True)
print(f"done: {done} new judgements in {mdir}")
