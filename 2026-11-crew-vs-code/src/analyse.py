"""Tables and hypothesis tests for crew-vs-code, from <out>/runs.jsonl (and judge.jsonl if present). Prints Markdown.

Rates with Wilson 95% intervals. Hypotheses (README), per model, outcome = resolved:
  H1 levels 1-3: state machine > crew (shared), one-sided
  H2 level 6:    crew (shared) > single agent, one-sided
  H3 all levels: crew (shared) != crew (note), two-sided
Permutation tests: arm labels shuffled within case x wording x account size, 10,000, seed 1; Holm over H1-H3 per model.
False action claim: the judge says the reply claims an action that the shop's log doesn't back (a refund claim is
backed by a refund or a cancellation; a hand-off claim by an escalation).
Usage: python3 -I analyse.py <out>   (reads runs.jsonl or runs.jsonl.gz, judge.jsonl or judge.jsonl.gz)
"""
import collections, gzip, json, math, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402,F401
from crewcases import CASES  # noqa: E402

MODELS = [("openai/gpt-6-luna", "Luna"), ("qwen/qwen3.7-flash", "Qwen")]
ARMS = [("statemachine", "State machine"), ("agent", "Single agent"), ("crew_shared", "Crew, shared history"),
        ("crew_note", "Crew, note only")]
LEVELS = {1: "1 simple", 2: "2 multi-step", 3: "3 branching", 4: "4 recovery", 5: "5 other requests", 6: "6 compound"}
BACK = {"refund": {"refund", "cancel"}, "replacement": {"replace"}, "cancel": {"cancel"}, "address_change": {"address"},
        "handed_to_team": {"escalate"}}
NEEDS_ACTION = {c["id"] for c in CASES if any(alt for alt in c["expect"]["actions"])}


def load(out, name):
    p = os.path.join(out, name)
    if os.path.exists(p):
        return [json.loads(l) for l in open(p)]
    if os.path.exists(p + ".gz"):
        return [json.loads(l) for l in gzip.open(p + ".gz", "rt")]
    return []


def key(r):
    return f"{r['case']}|{r['wording']}|{r['history']}|{r['arm']}|{r['model']}|{r['rep']}"


def wilson(k, n, z=1.96):
    if not n:
        return 0, 0
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0, c - h), min(1, c + h)


def rate(rs, f, ci=False):
    n = len(rs)
    if not n:
        return "–"
    k = sum(1 for r in rs if f(r))
    s = f"{100 * k / n:.0f}%"
    if ci:
        lo, hi = wilson(k, n)
        s += f" ({100 * lo:.0f}–{100 * hi:.0f})"
    return s


def perm(rs, a, b, two_sided=False, n=10000, seed=1):
    """Is arm a's resolved rate higher than arm b's (or different, two-sided)? Labels shuffled within strata."""
    rs = [r for r in rs if r["arm"] in (a, b)]
    def diff(rr):
        x = [r["outcome"] == "resolved" for r in rr if r["arm"] == a]
        y = [r["outcome"] == "resolved" for r in rr if r["arm"] == b]
        return sum(x) / len(x) - sum(y) / len(y)
    obs = diff(rs)
    groups = collections.defaultdict(list)
    for r in rs:
        groups[(r["case"], r["wording"], r["history"])].append(r)
    rng, hits = random.Random(seed), 0
    for _ in range(n):
        sh = []
        for g in groups.values():
            arms = [r["arm"] for r in g]
            rng.shuffle(arms)
            sh += [{**r, "arm": x} for r, x in zip(g, arms)]
        d = diff(sh)
        hits += (abs(d) >= abs(obs) - 1e-12) if two_sided else (d >= obs - 1e-12)
    return obs, (hits + 1) / (n + 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0] * len(ps), 0
    for rank, i in enumerate(order):
        run = max(run, min(1, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def main(out):
    runs = load(out, "runs.jsonl")
    judge = {j["key"]: j for j in load(out, "judge.jsonl")}
    for r in runs:
        j = judge.get(key(r))
        types = {a["type"] for a in r["actions"]}
        r["false_claims"] = None if j is None else [c for c, t in BACK.items() if j.get(c) is True and not types & t]
    by = collections.defaultdict(list)
    for r in runs:
        by[(r["arm"], r["model"])].append(r)
    rows = [(a, m, f"{an}, {mn}") for m, mn in MODELS for a, an in ARMS]
    P = print
    P("# crew-vs-code: analysis\n")
    P(f"{len(runs)} runs from `{os.path.basename(out.rstrip('/'))}`. Crashed: {sum(r['outcome'] == 'crashed' for r in runs)}. "
      f"Transport retries (OpenRouter): {sum(r.get('transport_retries', 0) for r in runs)}. "
      f"Judged: {sum(r['false_claims'] is not None for r in runs)}.\n")

    P("## Resolved, by level\n")
    P("Share of runs resolved (right state changes and every required fact in the reply); **higher is better**. Both "
      "wordings and both account sizes pooled; Wilson 95% interval for the total.\n")
    P("| Architecture | " + " | ".join(LEVELS.values()) + " | All |")
    P("| --- |" + " --- |" * (len(LEVELS) + 1))
    res = lambda r: r["outcome"] == "resolved"
    for a, m, name in rows:
        rs = by[(a, m)]
        P(f"| {name} | " + " | ".join(rate([r for r in rs if r["level"] == l], res) for l in LEVELS)
          + f" | **{rate(rs, res, True)}** |")

    P("\n## How runs ended\n")
    P("Share of all runs. Resolved: **higher is better**. Escalated (handed to a person when not required), wrong "
      "(missed action or missing information) and harmful (a refund, replacement, cancellation or address change the "
      "policy didn't call for): **lower is better**.\n")
    P("| Architecture | Resolved | Escalated | Wrong | Harmful | Harmful runs (count) |")
    P("| --- | --- | --- | --- | --- | --- |")
    for a, m, name in rows:
        rs = by[(a, m)]
        P(f"| {name} | " + " | ".join(rate(rs, lambda r, o=o: r["outcome"] == o) for o in ("resolved", "escalated", "wrong", "harmful"))
          + f" | {sum(r['outcome'] == 'harmful' for r in rs)} |")

    P("\n## False action claims\n")
    P("Share of runs whose reply tells the customer an action was taken (refund, replacement, cancellation, address "
      "change, handed to a team) that the shop's log shows wasn't; **lower is better**. By level, and the total with "
      "its Wilson 95% interval.\n")
    P("| Architecture | " + " | ".join(LEVELS.values()) + " | All | Most common claim |")
    P("| --- |" + " --- |" * (len(LEVELS) + 2))
    fc = lambda r: bool(r["false_claims"])
    for a, m, name in rows:
        rs = [r for r in by[(a, m)] if r["false_claims"] is not None]
        kinds = collections.Counter(c for r in rs for c in r["false_claims"]).most_common(1)
        P(f"| {name} | " + " | ".join(rate([r for r in rs if r["level"] == l], fc) for l in LEVELS)
          + f" | **{rate(rs, fc, True)}** | {kinds[0][0] + f' ({kinds[0][1]})' if kinds else '–'} |")

    P("\n## Crew handoffs\n")
    P("Handoffs per run (mean), and the share of runs on cases that need an action where the front desk replied "
      "without handing over (it can't act itself; **lower is better**).\n")
    P("| Crew | Handoffs per run | Front desk replied alone, action needed |")
    P("| --- | --- | --- |")
    for a, m, name in rows:
        if not a.startswith("crew"):
            continue
        rs = by[(a, m)]
        need = [r for r in rs if r["case"] in NEEDS_ACTION]
        P(f"| {name} | {st.mean(len(r['handoffs']) for r in rs):.2f} | {rate(need, lambda r: not r['handoffs'], True)} |")

    P("\n## Cost, calls, time and consistency\n")
    P("Mean cost per run (OpenRouter's billed cost) and per resolved run, mean model calls, median wall time; "
      "**lower is better**. Consistency: share of case × wording × account conditions where all repetitions ended the "
      "same way; **higher is better**.\n")
    P("| Architecture | Cost per run | Cost per resolved run | Model calls | Median seconds | Consistency | Total cost |")
    P("| --- | --- | --- | --- | --- | --- | --- |")
    for a, m, name in rows:
        rs = by[(a, m)]
        if not rs:
            continue
        cost = sum(r["cost"] for r in rs)
        nres = sum(res(r) for r in rs)
        cond = collections.defaultdict(set)
        for r in rs:
            cond[(r["case"], r["wording"], r["history"])].add(r["outcome"])
        P(f"| {name} | ${cost / len(rs):.5f} | {'$%.5f' % (cost / nres) if nres else '–'} | "
          f"{st.mean(r['llm_calls'] for r in rs):.1f} | {st.median(r['seconds'] for r in rs):.1f} | "
          f"{100 * sum(len(v) == 1 for v in cond.values()) / len(cond):.0f}% | ${cost:.2f} |")
    P(f"\nTotal: ${sum(r['cost'] for r in runs):.2f} for {len(runs)} runs.\n")

    P("## Hypotheses\n")
    P("Difference in resolved rate (first arm minus second, percentage points); permutation p within case × wording × "
      "account size (10,000, seed 1); Holm over H1–H3 within each model.\n")
    P("| Model | Hypothesis | Levels | Difference | p | Holm p |")
    P("| --- | --- | --- | --- | --- | --- |")
    tests = [("H1: state machine > crew (shared)", "statemachine", "crew_shared", {1, 2, 3}, False),
             ("H2: crew (shared) > single agent", "crew_shared", "agent", {6}, False),
             ("H3: crew (shared) ≠ crew (note)", "crew_shared", "crew_note", set(LEVELS), True)]
    summary = {}
    for m, mn in MODELS:
        rs = [r for r in runs if r["model"] == m]
        if not rs:
            continue
        got = [perm([r for r in rs if r["level"] in lv], a, b, two) for _, a, b, lv, two in tests]
        adj = holm([p for _, p in got])
        for (h, a, b, lv, two), (d, p), q in zip(tests, got, adj):
            P(f"| {mn} | {h} | {','.join(map(str, sorted(lv)))} | {100 * d:+.1f} | {p:.4f} | {q:.4f} |")
            summary[f"{mn} {h[:2]}"] = {"diff": d, "p": p, "holm": q}
    json.dump(summary, open(os.path.join(out, "hypotheses.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
