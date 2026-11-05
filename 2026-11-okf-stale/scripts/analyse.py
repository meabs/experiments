"""Analysis for okf-stale (README "Prediction and hypotheses" and "Detailed analysis plan"). Reads a stage directory
(grade.json and run.json per run, transcripts.jsonl, the judge's verdicts and my overrides) and writes analysis.md and
analysis.json beside them.

Unit: the run. Tests are one-sided permutation tests on run-level proportions, permuting the two arms' labels within
each ticket (10,000 permutations, seed 1); intervals are bootstrap 95% intervals resampling runs within each ticket;
H1 and H3 to H6 are Holm-adjusted together; H2 is a Clopper-Pearson interval.

Usage: python3 -I analyse.py <stage dir> [--second MODEL]
"""
import json, math, random, sys
from collections import defaultdict
from pathlib import Path

ARMS = ["A", "B", "D", "E", "F", "V"]
TASKS = ["F7", "F6", "F3"]
FACT = {"F7": "S1 template name", "F6": "S2 timeout and reference", "F3": "S3 rejected payments and the limit"}
NAME = {"A": "A, correct", "B": "B, stale", "D": "D, stale + metadata", "E": "E, stale + instruction",
        "F": "F, correct + instruction", "V": "V, no bundle"}
PRIMARY = "google/gemini-4-argon"
N_PERM, N_BOOT = 10000, 10000
PRICE = (0.20, 0.02, 1.20)  # gpt-5.6-luna list price per million tokens: input, cached input, output (OpenAI pricing page, 2026-11-05)


def cost(tok):
    inp, cached, out = tok.get("input", 0), tok.get("cache_read", 0), tok.get("output", 0)
    return ((inp - cached) * PRICE[0] + cached * PRICE[1] + out * PRICE[2]) / 1e6


def load(stage, second):
    runs = {}
    for g in sorted(stage.glob("feat-*/runs/*/*/codex/*/grade.json")):
        task, arm, rep = g.parts[-5], g.parts[-4], int(g.parts[-2])
        grade = json.load(open(g))
        run = json.load(open(g.parent / "run.json"))
        runs[(task, arm, rep)] = {"task": task, "arm": arm, "rep": rep, "outcome": grade["outcome"],
                                  "pass": grade["pass"], "build": grade["build"], "tokens": run.get("tokens") or {},
                                  "seconds": run.get("seconds") or 0, "status": run.get("status")}
    tr = stage / "transcripts.jsonl"
    if tr.exists():
        for l in tr.open():
            r = json.loads(l)
            k = (r["task"], r["arm"], r["rep"])
            if k in runs:
                runs[k]["tx"] = r
    over = json.load(open(stage / "judge-overrides.json")) if (stage / "judge-overrides.json").exists() else {}
    for model, field in ((PRIMARY, "judge"), (second, "judge2")):
        f = stage / f"judge-{(model or '').replace('/', '-')}.jsonl"
        if model and f.exists():
            for l in f.open():
                j = json.loads(l)
                t, a, r = j["run"].split("/")
                k = (t, a, int(r))
                if k in runs:
                    v = {"conflict": bool(j.get("conflict_reported")), "clarify": bool(j.get("clarification_asked"))}
                    if field == "judge" and j["run"] in over:
                        v.update(over[j["run"]])
                    runs[k][field] = v
    return list(runs.values())


def rate(rs, f):
    return sum(f(r) for r in rs) / len(rs) if rs else float("nan")


def strat_diff(rs, a, b, f):
    """Mean over tickets of (rate in a - rate in b), weighting tickets equally."""
    ds = []
    for t in TASKS:
        x = [r for r in rs if r["task"] == t and r["arm"] == a]
        y = [r for r in rs if r["task"] == t and r["arm"] == b]
        if x and y:
            ds.append(rate(x, f) - rate(y, f))
    return sum(ds) / len(ds) if ds else float("nan")


def perm_p(rs, a, b, f, seed=1):
    """One-sided p for (a - b) > 0, permuting arm labels within each ticket."""
    obs = strat_diff(rs, a, b, f)
    groups = {t: [r for r in rs if r["task"] == t and r["arm"] in (a, b)] for t in TASKS}
    rnd = random.Random(seed)
    hits = 0
    for _ in range(N_PERM):
        fake = []
        for t, g in groups.items():
            labels = [r["arm"] for r in g]
            rnd.shuffle(labels)
            fake += [dict(r, arm=l) for r, l in zip(g, labels)]
        if strat_diff(fake, a, b, f) >= obs - 1e-12:
            hits += 1
    return obs, (hits + 1) / (N_PERM + 1)


def boot_ci(rs, a, b, f, seed=1):
    rnd = random.Random(seed)
    cells = {(t, x): [r for r in rs if r["task"] == t and r["arm"] == x] for t in TASKS for x in (a, b)}
    vals = []
    for _ in range(N_BOOT):
        fake = []
        for (t, x), c in cells.items():
            fake += [rnd.choice(c) for _ in c] if c else []
        vals.append(strat_diff(fake, a, b, f))
    vals.sort()
    return vals[int(0.025 * N_BOOT)], vals[int(0.975 * N_BOOT) - 1]


def beta_ppf(q, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def betainc(a, b, x):
    # regularised incomplete beta by numerical integration (small n only)
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    n = 4000
    f = lambda t: t ** (a - 1) * (1 - t) ** (b - 1)
    h = x / n
    s = sum(f((i + 0.5) * h) for i in range(n)) * h
    tot = math.exp(math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))
    return s / tot


def clopper_pearson(k, n):
    lo = 0.0 if k == 0 else beta_ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(0.975, k + 1, n - k)
    return lo, hi


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def pct(x):
    return "n/a" if x != x else f"{100 * x:.0f}%"


def pts(x):
    return f"{100 * x:+.0f}"


def main(stage, second=None):
    stage = Path(stage)
    rs = load(stage, second)
    stale = lambda r: r["outcome"] == "stale"
    wrong = lambda r: r["outcome"] != "truth"
    ok = lambda r: r["pass"]
    conflict = lambda r: r.get("judge", {}).get("conflict", False)
    md = [f"# okf-stale analysis: {stage.name}", "", f"{len(rs)} runs.", ""]

    md += ["## Outcome on the stale fact", "",
           "Runs per arm and ticket: truth / stale / other (the change followed the code or contract / the stale "
           "statement / neither). For truth higher is better, for stale lower is better.", "",
           "| Arm | " + " | ".join(f"{t} ({FACT[t]})" for t in TASKS) + " | All |", "| --- |" + " --- |" * (len(TASKS) + 1)]
    for a in ARMS:
        cells = []
        for t in TASKS + [None]:
            c = [r for r in rs if r["arm"] == a and (t is None or r["task"] == t)]
            cells.append(f"{sum(r['outcome'] == 'truth' for r in c)} / {sum(r['outcome'] == 'stale' for r in c)} / "
                         f"{sum(r['outcome'] == 'other' for r in c)} (of {len(c)})")
        md.append(f"| {NAME[a]} | " + " | ".join(cells) + " |")
    md += ["", "Fully correct (every hidden and existing test; higher is better):", "",
           "| Arm | " + " | ".join(TASKS) + " | All |", "| --- |" + " --- |" * (len(TASKS) + 1)]
    for a in ARMS:
        cells = []
        for t in TASKS + [None]:
            c = [r for r in rs if r["arm"] == a and (t is None or r["task"] == t)]
            cells.append(f"{sum(ok(r) for r in c)}/{len(c)}")
        md.append(f"| {NAME[a]} | " + " | ".join(cells) + " |")

    hyps = [("H1", "E follows the stale fact less often than B", "B", "E", stale),
            ("H3", "B ends wrong (stale or other) more often than A", "B", "A", wrong),
            ("H4", "B is fully correct less often than V", "V", "B", ok),
            ("H5", "D follows the stale fact less often than B", "B", "D", stale),
            ("H6", "E reports the conflict more often than B", "E", "B", conflict)]
    res = []
    for h, text, a, b, f in hyps:
        d, p = perm_p(rs, a, b, f)
        lo, hi = boot_ci(rs, a, b, f)
        res.append({"h": h, "text": text, "a": a, "b": b, "diff": d, "p": p, "ci": [lo, hi]})
    for r, adj in zip(res, holm([r["p"] for r in res])):
        r["holm"] = adj
    e = [r for r in rs if r["arm"] == "E"]
    k = sum(stale(r) for r in e)
    cp = clopper_pearson(k, len(e)) if e else (float("nan"), float("nan"))
    md += ["", "## Hypotheses", "",
           "Differences are in percentage points, the first arm minus the second, averaged over the three tickets. "
           "One-sided permutation p, Holm-adjusted across H1 and H3 to H6.", "",
           "| # | Statement | Difference | 95% interval | p | Holm p |", "| --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['h']} | {r['text']} ({r['a']} − {r['b']}) | {pts(r['diff'])} | {pts(r['ci'][0])} to "
                  f"{pts(r['ci'][1])} | {r['p']:.4f} | {r['holm']:.4f} |")
    md += ["", f"**H2** (E rarely follows it): E followed the stale fact in {k} of {len(e)} runs ({pct(k / len(e) if e else float('nan'))}); "
           f"95% Clopper-Pearson interval {pct(cp[0])} to {pct(cp[1])}; supported if the upper end is below 25%: "
           f"**{'yes' if cp[1] < 0.25 else 'no'}**.", ""]

    md += ["## How the runs decided (from the transcripts)", "",
           "Share of runs (higher means more checking):", "",
           "| Arm | Opened okf/ | Opened the ticket's source of truth | ...before the first edit | Opened contracts/ | Ran `date` | Mentioned freshness | Conflict reported (judge) | Asked the user |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in ARMS:
        c = [r for r in rs if r["arm"] == a and "tx" in r]
        tx = lambda f: pct(rate(c, lambda r: f(r["tx"])))
        md.append(f"| {NAME[a]} | {tx(lambda x: x['okf_read'])} | {tx(lambda x: x['truth_source_first_command'] is not None)} | "
                  f"{tx(lambda x: x['truth_source_before_edit'])} | {tx(lambda x: x['opened_contracts'])} | "
                  f"{tx(lambda x: x['ran_date'])} | {tx(lambda x: x['mentions_freshness'])} | "
                  f"{pct(rate(c, conflict))} | {pct(rate(c, lambda r: r.get('judge', {}).get('clarify', False)))} |")
    md += ["", "Outcome by whether the run opened the ticket's source of truth before its first edit (runs following "
           "the stale fact / runs):", "", "| Arm | Opened it first | Didn't |", "| --- | --- | --- |"]
    for a in ARMS:
        c = [r for r in rs if r["arm"] == a and "tx" in r]
        y = [r for r in c if r["tx"]["truth_source_before_edit"]]
        n = [r for r in c if not r["tx"]["truth_source_before_edit"]]
        md.append(f"| {NAME[a]} | {sum(map(stale, y))}/{len(y)} | {sum(map(stale, n))}/{len(n)} |")

    md += ["", "## Exploratory: the instruction's cost on a correct bundle (F against A)", ""]
    for name, f in (("fully correct", ok), ("truth", lambda r: r["outcome"] == "truth")):
        d, p = perm_p(rs, "F", "A", f)
        md.append(f"- {name}: F − A {pts(d)} points (one-sided p for F > A {p:.3f})")

    md += ["", "## Tokens, time and cost", "",
           "Mean per run: input (of which new, not cached) / output tokens; seconds; list-price cost (lower is cheaper).", "",
           "| Arm | " + " | ".join(TASKS) + " | Seconds | Cost per run | Cost per fully correct run |",
           "| --- |" + " --- |" * (len(TASKS) + 3)]
    tok_rows = {}
    for a in ARMS:
        cells = []
        for t in TASKS:
            c = [r for r in rs if r["arm"] == a and r["task"] == t]
            if not c:
                cells.append("n/a")
                continue
            inp = sum(r["tokens"].get("input", 0) for r in c) / len(c)
            cached = sum(r["tokens"].get("cache_read", 0) for r in c) / len(c)
            out = sum(r["tokens"].get("output", 0) for r in c) / len(c)
            tok_rows[f"{a}/{t}"] = {"input": inp, "cached": cached, "output": out}
            cells.append(f"{inp / 1000:.0f}k ({(inp - cached) / 1000:.0f}k new) / {out / 1000:.1f}k")
        c = [r for r in rs if r["arm"] == a]
        tot = sum(cost(r["tokens"]) for r in c)
        good = sum(map(ok, c))
        md.append(f"| {NAME[a]} | " + " | ".join(cells) + f" | {rate(c, lambda r: r['seconds']):.0f} | "
                  f"${tot / len(c) if c else 0:.3f} | {'$%.3f' % (tot / good) if good else 'n/a'} |")

    if second:
        both = [r for r in rs if "judge" in r and "judge2" in r]
        agree = sum(r["judge"]["conflict"] == r["judge2"]["conflict"] for r in both)
        md += ["", "## Robustness", "", f"- Second judge (`{second}`) on conflict reported: agrees on {agree} of {len(both)} runs."]
        d, p = perm_p([dict(r, judge=r.get("judge2", {})) for r in rs], "E", "B", conflict)
        md.append(f"- H6 under the second judge: E − B {pts(d)} points, one-sided p {p:.4f}.")
    alt = lambda r: r["outcome"] != "truth"
    d, p = perm_p(rs, "B", "E", alt)
    md.append(f"- H1 with *other* counted as stale: B − E {pts(d)} points, one-sided p {p:.4f}.")

    (stage / "analysis.md").write_text("\n".join(md) + "\n")
    (stage / "analysis.json").write_text(json.dumps({"hypotheses": res, "h2": {"k": k, "n": len(e), "ci": cp},
                                                     "tokens": tok_rows}, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    a = sys.argv[1:]
    s = None
    if "--second" in a:
        i = a.index("--second"); s = a[i + 1]; del a[i:i + 2]
    main(a[0], s)
