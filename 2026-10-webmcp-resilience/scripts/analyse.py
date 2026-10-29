"""Analysis for webmcp-resilience, fixed before the measured runs (README, "Hypotheses and analysis").

A run passes if it finished (status ok) and verify.sh accepted it (verified): every hidden case passed and the files
that stand in for the server, network and browser are unchanged. Arms are compared by the mean over the six tasks of
each task's pass rate, so every task counts equally.

- H1 tool > plain, H2 tool-recipes > tool (passes). One-sided permutation tests, arm labels shuffled within each task,
  100,000 shuffles, seed 1. Effect intervals: bootstrap within tasks, 10,000 resamples, seed 1. Holm over H1 and H2
  at alpha 0.05.
- Secondary (no tests): tool-recipes vs plain; hidden cases passed; false success claims; use of the tool; own browser
  checks; wall time, tokens and cost at list prices.

Usage: python3 -I analyse.py <out dir> > results/analysis.md   (out dir holds <arm>/runs/<task>/<arm>/codex/<rep>/)
"""
import glob, gzip, json, os, random, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-skills-impact", "scripts"))
from stats import holm  # noqa: E402

ARMS = ["plain", "tool", "tool-recipes"]
TASKS = ["charge-no-order", "double-add", "half-saved", "last-seat", "lost-update", "stale-quantity"]
PERMS, BOOTS, SEED = 100_000, 10_000, 1
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}  # gpt-5.6-luna list prices, $ per million tokens
TOOL_RE = re.compile(r"(^|[\s/;&|(])webmcp\s+(run|validate|replay|preflight|demo-race|agent-server)\b")
BROWSER_RE = re.compile(r"playwright|chromium", re.I)


def read(path):
    if os.path.exists(path):
        return open(path, errors="replace").read()
    if os.path.exists(path + ".gz"):
        return gzip.open(path + ".gz", "rt", errors="replace").read()
    return ""


def load(out):
    runs = []
    for f in glob.glob(os.path.join(out, "*", "runs", "*", "*", "codex", "*", "run.json")):
        r = json.load(open(f))
        if r["arm"] not in ARMS or r["question"] not in TASKS:
            continue
        d = os.path.dirname(f)
        hidden = json.loads(read(os.path.join(d, "hidden.json")) or "{}")
        protected = json.loads(read(os.path.join(d, "protected.json")) or "{}")
        calls = [c.get("text", "") for c in r.get("tool_calls") or []]
        tok = r.get("tokens") or {}
        cached = tok.get("cache_read") or 0
        cost = ((tok.get("input", 0) - cached) * PRICE["input"] + cached * PRICE["cached"]
                + tok.get("output", 0) * PRICE["output"]) / 1e6
        runs.append({
            "task": r["question"], "arm": r["arm"], "rep": r["rep"], "status": r["status"],
            "pass": 1 if r["status"] == "ok" and r.get("verified") else 0,
            "cases": (hidden.get("passed"), hidden.get("total")),
            "protected": protected.get("changed") or [],
            "seconds": r["seconds"], "tokens": tok.get("total"), "cost": cost, "turns": r.get("turns"),
            "claim": r.get("claim_match"),
            "used_tool": any(TOOL_RE.search(c) for c in calls),
            "own_browser": any(BROWSER_RE.search(c) and not TOOL_RE.search(c) for c in calls),
            "left": "code/experiments" in read(os.path.join(d, "raw.out")),
        })
    return runs


def by_task(runs, arm, key):
    return {t: [r[key] for r in runs if r["arm"] == arm and r["task"] == t] for t in TASKS}


def stat(a, b):
    ts = [t for t in TASKS if a[t] and b[t]]
    return st.mean(st.mean(a[t]) - st.mean(b[t]) for t in ts) if ts else float("nan")


def perm_greater(a, b, rng):
    """One-sided p for stat(a, b) > 0, labels shuffled within each task."""
    obs = stat(a, b)
    hits = 0
    for _ in range(PERMS):
        pa, pb = {}, {}
        for t in TASKS:
            pool = a[t] + b[t]
            rng.shuffle(pool)
            pa[t], pb[t] = pool[: len(a[t])], pool[len(a[t]):]
        if stat(pa, pb) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (PERMS + 1)


def boot(a, b, rng):
    vals = []
    for _ in range(BOOTS):
        ra = {t: [rng.choice(a[t]) for _ in a[t]] if a[t] else [] for t in TASKS}
        rb = {t: [rng.choice(b[t]) for _ in b[t]] if b[t] else [] for t in TASKS}
        vals.append(stat(ra, rb))
    vals.sort()
    return vals[int(0.025 * BOOTS)], vals[int(0.975 * BOOTS) - 1]


def pts(x):
    return f"{x * 100:+.1f} points"


def main(out):
    runs = load(out)
    rng = random.Random(SEED)
    print("# webmcp-resilience: analysis\n")
    print(f"{len(runs)} runs from `{out}`. A pass means the run finished, every hidden case passed, and the files standing in "
          "for the server, network and browser were left unchanged.\n")

    print("## Passes by arm and task (higher is better)\n")
    print("| Task | " + " | ".join(f"`{a}`" for a in ARMS) + " |")
    print("| --- |" + " --- |" * len(ARMS))
    for t in TASKS:
        print(f"| {t} | " + " | ".join(f"{sum(v)}/{len(v)}" for v in (by_task(runs, a, 'pass')[t] for a in ARMS)) + " |")
    print("| **Total** | " + " | ".join(
        f"**{sum(r['pass'] for r in runs if r['arm'] == a)}/{sum(r['arm'] == a for r in runs)}**" for a in ARMS) + " |\n")

    print("## Hypotheses (one-sided, Holm-adjusted together)\n")
    print("Effect: the mean over tasks of the difference in pass rate, in percentage points (positive favours the first arm).\n")
    hyp = [("H1", "`tool` passes more than `plain`", "tool", "plain"),
           ("H2", "`tool-recipes` passes more than `tool`", "tool-recipes", "tool")]
    res = []
    for hid, text, x, y in hyp:
        a, b = by_task(runs, x, "pass"), by_task(runs, y, "pass")
        res.append((hid, text, stat(a, b), *boot(a, b, rng), perm_greater(a, b, rng)))
    print("| # | Hypothesis | Effect (95% interval) | p | Holm p | Verdict |")
    print("| --- | --- | --- | --- | --- | --- |")
    for (hid, text, eff, lo, hi, p), q in zip(res, holm([r[-1] for r in res])):
        print(f"| {hid} | {text} | {pts(eff)} ({pts(lo)} to {pts(hi)}) | {p:.4f} | {q:.4f} | "
              f"{'confirmed' if q < 0.05 else 'no measurable difference'} |")
    print()

    print("## Did the arms happen as designed?\n")
    for a in ["tool", "tool-recipes"]:
        rs = [r for r in runs if r["arm"] == a]
        n = sum(r["used_tool"] for r in rs)
        ok = rs and n >= 0.75 * len(rs)
        print(f"- `{a}`: {n} of {len(rs)} runs ran WebMCP Resilience (`webmcp run`, `validate`, `replay`, ...)"
              f"{'' if ok else ' (fewer than three quarters: the arm did not happen as designed)'}.")
    n = sum(r["used_tool"] for r in runs if r["arm"] == "plain")
    print(f"- `plain`: {n} runs ran WebMCP Resilience (should be 0: it is not installed there).")
    left = [f"{r['task']} {r['arm']} {r['rep']}" for r in runs if r["left"]]
    print(f"- Runs that named the experiments folder (where the hidden tests are): {len(left)}"
          f"{' (' + ', '.join(left) + ')' if left else ''}.")
    prot = [f"{r['task']} {r['arm']} {r['rep']} ({', '.join(r['protected'])})" for r in runs if r["protected"]]
    print(f"- Runs that changed a file standing in for the server, network or browser (a fail): {len(prot)}"
          f"{' (' + '; '.join(prot) + ')' if prot else ''}.\n")

    print("## Secondary (not tested)\n")
    a, b = by_task(runs, "tool-recipes", "pass"), by_task(runs, "plain", "pass")
    print(f"- `tool-recipes` against `plain`, passes: {pts(stat(a, b))}.\n")
    print("| Arm | Runs | Hidden cases passed (higher is better) | False success claims (lower is better) | Wrote own browser checks "
          "| Median wall time (lower is better) | Median tokens (lower is better) | Mean cost per run, $ list price (lower is better) | Timeouts |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for arm in ARMS:
        rs = [r for r in runs if r["arm"] == arm]
        if not rs:
            continue
        cp = sum(r["cases"][0] or 0 for r in rs)
        ct = sum(r["cases"][1] or 0 for r in rs)
        fails = [r for r in rs if not r["pass"]]
        false = sum(r["claim"] == "false_pass" for r in rs)
        tok = [r["tokens"] for r in rs if r["tokens"]]
        print(f"| `{arm}` | {len(rs)} | {cp}/{ct} | {false} of {len(fails)} failed runs | {sum(r['own_browser'] for r in rs)} | "
              f"{st.median(r['seconds'] for r in rs):.0f} s | {st.median(tok) / 1000:.0f}k | {st.mean(r['cost'] for r in rs):.3f} | "
              f"{sum(r['status'] == 'timeout' for r in rs)} |")
    print("\nA false success claim: the agent's closing verification line said its check passed, but the hidden tests failed.")


if __name__ == "__main__":
    main(sys.argv[1])
