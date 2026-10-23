"""Asks the model every variant of every item (README, "Procedure"). Each answer is one `codex exec` call, read-only
sandbox, in an empty folder inside bubblewrap (setup/codex-bwrap.sh of 2026-10-test-skill-local), as in 2026-10-diff-judge.

  model local : qwen3.8:27b via Ollama (the local profile)        model hosted : gpt-5.6-luna (CODEX_PROFILE=hosted)
  variants    : GSM8K orig, numbers, names, both (names and both exist only for items with a swappable first name);
                HumanEval orig, renamed (items with an entry point; graded by their tests in grade_code.py)

Order: every (item, variant) pair in one order shuffled with random.Random(1); the same order for both models. An answer
already on disk is skipped, so the script resumes after an interruption. Writes <out>/<model>/<variant>/<idx>/:
result.json (answer, correct, seconds, usage, tool calls), raw.out (Codex events), raw.err.
Usage: python3 -I run.py <out dir> <local|hosted> [items.json] [--variants orig,numbers,names,both,renamed] [--limit n]
"""
import argparse, json, os, random, re, subprocess, sys, time
from datetime import datetime, timezone
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE); sys.path.insert(0, HERE)
from grade_code import run_tests  # noqa: E402
WRAP = os.path.expanduser("~/code/benchmark/local-setup/codex-bwrap.sh")
MODEL = {"local": "qwen3.8:27b", "hosted": "gpt-5.6-luna"}
TIMEOUT = 600
PROMPT = {k: open(os.path.join(N, "arms", f"{k}-prompt.md")).read() for k in ("gsm8k", "humaneval")}
CODE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)
ANSWER = re.compile(r"ANSWER:\s*\**\s*\$?\s*(-?[\d,]*\.?\d+)")

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("model", choices=MODEL); ap.add_argument("items", nargs="?", default=os.path.join(N, "items", "gsm8k-twins.json"))
ap.add_argument("--variants", default="orig,numbers,names,both,renamed"); ap.add_argument("--limit", type=int)
a = ap.parse_args()


def parse(text):
    msg, usage, tools = "", {}, 0
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
    m = ANSWER.findall(msg)
    return (m[-1].replace(",", "") if m else None), usage, tools, msg


def same(ans, ref):
    try:
        return F(ans) == F(ref)
    except (ValueError, ZeroDivisionError):
        return False


items = json.load(open(a.items))
pairs = [(i, v) for i in range(len(items)) for v in a.variants.split(",") if items[i].get(v)]
random.Random(1).shuffle(pairs)
if a.limit:
    pairs = pairs[:a.limit]
mdir = os.path.join(os.path.abspath(a.out), a.model)
bench = "humaneval" if "entry_orig" in items[0] else "gsm8k"
done = 0
for n, (i, v) in enumerate(pairs, 1):
    item = items[i]
    d = os.path.join(mdir, bench, v, str(item["idx"]))
    if os.path.exists(os.path.join(d, "result.json")):
        continue
    work = os.path.join(mdir, "work", f"{bench}_{v}_{item['idx']}")
    os.makedirs(work, exist_ok=True); os.makedirs(d, exist_ok=True)
    env = dict(os.environ, TRIAL_OUT=mdir, TRIAL_ID=f"{bench}_{v}_{item['idx']}")
    if a.model == "hosted":
        env["CODEX_PROFILE"] = "hosted"
    cmd = ["bash", WRAP, "exec", "-s", "read-only", "--skip-git-repo-check", "--json", "--model", MODEL[a.model],
           "-c", 'model_reasoning_effort="low"', PROMPT[bench].replace("{question}", item[v].strip())]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds"); t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
        out, err, rc, timed_out = r.stdout, r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as e:
        out, err, rc, timed_out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "", None, True
    secs = round(time.monotonic() - t0, 1)
    ans, usage, tools, msg = parse(out)
    if bench == "gsm8k":
        ref = item["answer_orig"] if v in ("orig", "names") else item["answer_twin"]
        ok, detail = (same(ans, ref) if ans is not None else False), ""
    else:
        blocks = CODE.findall(msg)
        ans = blocks[-1] if blocks else None
        ref = item[f"entry_{v}"]
        ok, detail = run_tests(item[v] + "\n" + ans, item[f"test_{v}"], ref) if ans is not None else (False, "no code block")
    open(os.path.join(d, "raw.out"), "w").write(out); open(os.path.join(d, "raw.err"), "w").write(err or "")
    rec = dict(idx=item["idx"], variant=v, model=MODEL[a.model], reference=str(ref), answer=ans,
               correct=ok, grade_detail=detail, seconds=secs, started=started, exit_code=rc,
               timed_out=timed_out, usage=usage, tool_calls=tools, steps=item.get("steps"), final_message=msg)
    json.dump(rec, open(os.path.join(d, "result.json"), "w"), indent=1)
    done += 1
    print(f"[{n}/{len(pairs)}] {a.model} {v} {item['idx']} ref={ref} answer={ans if bench == 'gsm8k' else ('code' if ans else None)} correct={ok} {secs}s", flush=True)
print(f"done: {done} new answers in {mdir}")
