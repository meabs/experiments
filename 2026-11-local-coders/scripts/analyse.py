"""Analysis for local-coders (the design's measures and hypotheses). Written before the main run's results were read.

  python3 -I analyse.py            main run: $LC_WORK/main/m*  ->  results/analysis.md, results/summary.json
  python3 -I analyse.py --pilot    pilot:    $LC_WORK/pilot/p*  ->  results/pilot.md (drop and ceiling checks)

Per run (meta.json, grade.json, ws.diff, final.md, power.csv, events.jsonl, judge.json):
  passed         finished within 30 minutes and the hidden test passes (grade.json "passed", not timed out)
  drove          changed at least one file and ended with a final message
  false_claim    the judge codes the final message as a "success" claim and the run didn't pass; results/handcheck.json
                 ({"run": true|false}) overrides the label after the hand check
  minutes, Wh    wall time; APU package power integrated over the run
  tokens         input + output, from Codex's turn.completed events
Tests: each model against the reference (qwen3.8:27b), two-sided, labels shuffled within task (10,000, seed 1), Holm
over the models present; Wilson 95% intervals; everything else descriptive.
"""
import glob, json, math, os, random, statistics, sys

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.environ.get("LC_WORK", os.path.expanduser("~/code/benchmark/lc-work"))
REF = "qwen3.8:27b"
ORDER = ["qwen3.8:27b", "qwen3-coder:30b", "devstral-small-2:24b", "gpt-oss:20b", "flint:40b"]
SETS = {"S": "storefront", "J": "accounts API"}
BAR_PASS, BAR_MIN = 10 / 12, 10.0   # "good enough": >= 10 of 12 on each set, median run <= 10 minutes


def energy(path):
    try:
        pts = [tuple(map(float, l.split(","))) for l in open(path).read().split("\n")[1:] if l.strip()]
    except (OSError, ValueError):
        return None
    if len(pts) < 2:
        return None
    return sum((t2 - t1) * (w1 + w2) / 2 for (t1, w1), (t2, w2) in zip(pts, pts[1:])) / 3600


def tokens(path):
    n = 0
    for line in open(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "turn.completed":
            n += e["usage"].get("input_tokens", 0) + e["usage"].get("output_tokens", 0)
    return n


def row(d, hand):
    p = lambda f: os.path.join(d, f)
    m, g = json.load(open(p("meta.json"))), json.load(open(p("grade.json")))
    final = open(p("final.md")).read().strip() if os.path.exists(p("final.md")) else ""
    diff = open(p("ws.diff")).read().strip() if os.path.exists(p("ws.diff")) else ""
    passed = bool(g.get("passed")) and not m.get("timed_out")
    claim = json.load(open(p("judge.json"))).get("claim") if os.path.exists(p("judge.json")) else None
    run = os.path.basename(d)
    false_claim = None if claim is None else (claim == "success" and not passed)
    if run in hand:
        false_claim = bool(hand[run])
    return {"run": run, "model": m["model"], "task": m["task"], "set": m["set"], "passed": passed,
            "drove": bool(diff) and bool(final) and final != "(no message)", "timed_out": bool(m.get("timed_out")),
            "minutes": (m.get("seconds") or 0) / 60, "wh": energy(p("power.csv")), "tokens": tokens(p("events.jsonl")),
            "claim": claim, "false_claim": false_claim}


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    c = (k / n + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(k / n * (1 - k / n) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0, c - h), min(1, c + h)


def perm2(rows, a, b, n=10000, seed=1):
    """Two-sided: does model a's pass rate differ from model b's? Labels shuffled within task."""
    rs = [r for r in rows if r["model"] in (a, b)]
    rate = lambda rr, mod: [x["passed"] for x in rr if x["model"] == mod]
    def diff(rr):
        x, y = rate(rr, a), rate(rr, b)
        return sum(x) / len(x) - sum(y) / len(y)
    if not rate(rs, a) or not rate(rs, b):
        return float("nan"), float("nan")
    obs, rng, by, hits = diff(rs), random.Random(seed), {}, 0
    for r in rs:
        by.setdefault(r["task"], []).append(r)
    for _ in range(n):
        sh = []
        for grp in by.values():
            labels = [r["model"] for r in grp]
            rng.shuffle(labels)
            sh += [{**r, "model": l} for r, l in zip(grp, labels)]
        if abs(diff(sh)) >= abs(obs) - 1e-12:
            hits += 1
    return obs, (hits + 1) / (n + 1)


def holm(ps):
    order, adj, run = sorted(range(len(ps)), key=lambda i: ps[i]), [0] * len(ps), 0
    for rank, i in enumerate(order):
        run = max(run, min(1, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def frac(rr, key):
    k, n = sum(1 for r in rr if r[key]), len(rr)
    lo, hi = wilson(k, n)
    return f"{k} / {n} ({lo:.0%}–{hi:.0%})" if n else "–"


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else float("nan")


def leaderboard(rows, models, out):
    out.extend(["## Leaderboard", "",
                "Passes: runs that finished within 30 minutes with the hidden test passing, of all runs (higher is better; "
                "Wilson 95% in brackets). Minutes: median wall time per run (lower is better). Wh: median energy per run, "
                "and total energy divided by passes (lower is better; – if no pass). \"Good enough\": at least 10 of 12 "
                "on each set and a median run of 10 minutes or less.", "",
                "| Model | Passes, storefront | Passes, accounts API | Passes, all | Drove Codex | Timeouts | Median minutes | Median Wh | Wh per pass | Median tokens | Good enough |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
    for mod in models:
        rr = [r for r in rows if r["model"] == mod]
        s, j = [r for r in rr if r["set"] == "S"], [r for r in rr if r["set"] == "J"]
        passes = sum(r["passed"] for r in rr)
        whs = [r["wh"] for r in rr if r["wh"] is not None]
        ok = (s and j and sum(r["passed"] for r in s) / len(s) >= BAR_PASS and sum(r["passed"] for r in j) / len(j) >= BAR_PASS
              and med(r["minutes"] for r in rr) <= BAR_MIN)
        out.append(f"| `{mod}` | {frac(s, 'passed')} | {frac(j, 'passed')} | {frac(rr, 'passed')} | "
                   f"{sum(r['drove'] for r in rr)} / {len(rr)} | {sum(r['timed_out'] for r in rr)} | "
                   f"{med(r['minutes'] for r in rr):.1f} | {med(whs):.1f} | "
                   f"{(sum(whs) / passes) if passes and whs else float('nan'):.1f} | {med(r['tokens'] for r in rr):,.0f} | "
                   f"{'yes' if ok else 'no'} |".replace("nan", "–"))
    out.append("")


def per_task(rows, models, out):
    tasks = sorted({r["task"] for r in rows}, key=lambda t: ({r["task"]: r["set"] for r in rows}[t], t))
    out.extend(["## Passes by task", "", "Passing runs of each task (higher is better).", "",
                "| Model | " + " | ".join(tasks) + " |", "| --- | " + " | ".join("---" for _ in tasks) + " |"])
    for mod in models:
        cells = []
        for t in tasks:
            rr = [r for r in rows if r["model"] == mod and r["task"] == t]
            cells.append(f"{sum(r['passed'] for r in rr)} / {len(rr)}" if rr else "–")
        out.append(f"| `{mod}` | " + " | ".join(cells) + " |")
    out.append("")


def main(pilot):
    hand_path = os.path.join(E, "results", "handcheck.json")
    hand = json.load(open(hand_path)) if os.path.exists(hand_path) else {}
    dirs = sorted(d for d in glob.glob(os.path.join(W, "pilot" if pilot else "main", "p[0-9]*" if pilot else "m[0-9]*"))
                  if os.path.exists(os.path.join(d, "grade.json")))
    rows = [row(d, hand) for d in dirs]
    models = [m for m in ORDER if any(r["model"] == m for r in rows)]
    out = [f"# local-coders: {'pilot' if pilot else 'analysis'}", "", f"{len(rows)} graded runs.", ""]
    leaderboard(rows, models, out)
    per_task(rows, models, out)
    if pilot:
        out.extend(["## Pilot checks", ""])
        for mod in models:
            rr = [r for r in rows if r["model"] == mod]
            edited = sum(1 for r in rr if r["drove"])
            out.append(f"- `{mod}`: drove Codex in {edited} of {len(rr)} runs" +
                       (" (drop rule: no edit in all 8 runs)" if edited == 0 and len(rr) >= 8 else "") + ".")
        s = [r for r in rows if r["set"] == "S"]
        out.extend(["", f"- Ceiling on the storefront set: {'yes, every' if s and all(r['passed'] for r in s) else 'no, not every'} "
                    "model passed every storefront pilot run.", ""])
        name = "pilot.md"
        summary = None
    else:
        others = [m for m in models if m != REF]
        res = [perm2(rows, m, REF) for m in others]
        adj = holm([p for _, p in res]) if res else []
        out.extend(["## Hypotheses", "", f"Each model against `{REF}`. Difference: pass rate minus the reference's "
                    "(positive: the model passes more often). Two-sided permutation test, labels shuffled within task; "
                    "Holm over the models tested. \"No measurable difference\" where Holm p ≥ 0.05.", "",
                    "| Model | Difference in pass rate | p | Holm p |", "| --- | --- | --- | --- |"])
        for m, (d, p), a in zip(others, res, adj):
            out.append(f"| `{m}` | {d:+.2f} | {p:.4f} | {a:.4f} |")
        coded = [r for r in rows if r["false_claim"] is not None]
        out.extend(["", "## False success claims", "",
                    "Runs whose final message claims the work is done or passes while the hidden test fails, of runs coded "
                    "(lower is better). Every positive is hand-checked.", "",
                    "| Model | False success claims | Claimed success | Unchecked positives |", "| --- | --- | --- | --- |"])
        for mod in models:
            rr = [r for r in coded if r["model"] == mod]
            out.append(f"| `{mod}` | {frac(rr, 'false_claim')} | {sum(r['claim'] == 'success' for r in rr)} / {len(rr)} | "
                       f"{sum(1 for r in rr if r['false_claim'] and r['run'] not in hand)} |")
        out.append("")
        name = "analysis.md"
        summary = {"rows": rows, "hypotheses": [{"model": m, "diff": d, "p": p, "holm": a}
                                                for m, (d, p), a in zip(others, res, adj)]}
    os.makedirs(os.path.join(E, "results"), exist_ok=True)
    open(os.path.join(E, "results", name), "w").write("\n".join(out))
    if summary:
        json.dump(summary, open(os.path.join(E, "results", "summary.json"), "w"), indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main("--pilot" in sys.argv[1:])
