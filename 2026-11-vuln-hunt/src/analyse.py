"""Tables and hypothesis tests for vuln-hunt. Prints Markdown.

Usage: python3 -I analyse.py <main dir>
Reads <main dir>/key.json, <run>/meta.json, <run>/FINDINGS.json, judge.jsonl and, if present,
results/overrides.json (my hand labels where I disagree with the judge: {"run|index": "V07" | "none" | ...}, and
{"also": ["run|index", ...]} for "also" matches I accept).

A run finds a vulnerability if one of its findings has it as the (hand-checked) main match, or as an accepted "also".
Precision = findings matching a planted vulnerability / (all findings - real issues outside the key).
Tests (README): the unit is the vulnerability. H1 (B > A), H2 (C > B), H4 (A2 > A) on the 14 hard and very-hard
vulnerabilities: per-vulnerability detection rates over 10 runs, paired differences, exact one-sided sign-flip
permutation test, bootstrap 95% interval of the mean difference (10,000, seed 1). H3 (precision B > A): one-sided
permutation of arm labels over the 20 runs (10,000, seed 1). Holm over H1-H4. All with Luna.
"""
import collections, itertools, json, os, random, statistics, sys
from pathlib import Path

E = Path(__file__).resolve().parent.parent
KEY = json.load(open(E / "key" / "answer_key.json"))
V = {v["id"]: v for v in KEY["vulnerabilities"]}
D = {d["id"] for d in KEY["decoys"]}
TIERS = ["easy", "medium", "hard", "very hard"]
HARD = [v for v in V if V[v]["tier"] in ("hard", "very hard")]
OWASP = {"A01": "Broken Access Control", "A02": "Security Misconfiguration", "A03": "Software Supply Chain Failures",
         "A04": "Cryptographic Failures", "A05": "Injection", "A06": "Insecure Design",
         "A07": "Authentication Failures", "A08": "Software or Data Integrity Failures",
         "A09": "Security Logging & Alerting Failures", "A10": "Mishandling of Exceptional Conditions"}
ARMS = [("A", "luna", "A. Codex"), ("A2", "luna", "A2. Codex + checklist"), ("B", "luna", "B. Strands specialist"),
        ("C", "luna", "C. Strands team (Graph)"), ("D", "luna", "D. Strands swarm"),
        ("B", "qwen", "B. Strands specialist, Qwen"), ("C", "qwen", "C. Strands team, Qwen")]
PRICE = {"luna": (0.20, 0.02, 1.20), "qwen": (0.03, 0.006, 0.13)}   # $ per million: input, cached input, output


def load(main):
    main = Path(main)
    key = json.load(open(main / "key.json"))
    ov_path = E / "results" / "overrides.json"
    ov = json.load(open(ov_path)) if ov_path.exists() else {}
    also_ok = set(ov.pop("also", []))
    labels = collections.defaultdict(list)
    for l in open(main / "judge.jsonl"):
        j = json.loads(l)
        k = f"{j['run']}|{j['index']}"
        labels[j["run"]].append({"k": k, "match": ov.get(k, j["match"]),
                                 "also": [a for a in j.get("also") or [] if k in also_ok]})
    runs = []
    for run, k in key.items():
        m = json.load(open(main / run / "meta.json"))
        ls = labels.get(run, [])
        found = {l["match"] for l in ls if l["match"] in V} | {a for l in ls for a in l["also"] if a in V}
        n = len(ls)
        matched = sum(l["match"] in V for l in ls)
        other = sum(l["match"] == "other_real" for l in ls)
        decoys = sum(l["match"] in D for l in ls)
        wrong = sum(l["match"] == "none" for l in ls)
        u = m.get("usage") or {}
        pi, pc, po = PRICE[k["model"]]
        cost = ((u.get("input", 0) - u.get("cached", 0)) * pi + u.get("cached", 0) * pc + u.get("output", 0) * po) / 1e6
        runs.append({"run": run, **k, "found": found, "findings": n, "matched": matched, "other": other,
                     "decoys": decoys, "wrong": wrong, "dups": matched - len({l["match"] for l in ls if l["match"] in V}),
                     "precision": matched / (n - other) if n - other else None, "cost": cost,
                     "seconds": m.get("seconds"), "tokens": u.get("input", 0) + u.get("output", 0),
                     "failed": m.get("findings") is None, "status": u.get("status"), "handoffs": u.get("handoffs") or u.get("order")})
    return runs


def sel(runs, arm, model):
    return [r for r in runs if r["arm"] == arm and r["model"] == model]


def rate(rs, vid):
    return sum(vid in r["found"] for r in rs) / len(rs) if rs else float("nan")


def signflip(diffs):
    """Exact one-sided sign-flip test of mean(diffs) > 0."""
    obs = sum(diffs)
    nz = [d for d in diffs if d]
    ge = sum(1 for s in itertools.product((1, -1), repeat=len(nz)) if sum(a * b for a, b in zip(s, nz)) >= obs - 1e-12)
    return ge / 2 ** len(nz)


def boot(diffs, n=10000, seed=1):
    rnd = random.Random(seed)
    ms = sorted(statistics.mean(rnd.choices(diffs, k=len(diffs))) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def perm_runs(x, y, n=10000, seed=1):
    """One-sided: mean(x) > mean(y), arm labels shuffled over the pooled runs."""
    rnd = random.Random(seed)
    obs = statistics.mean(x) - statistics.mean(y)
    pool, k, ge = x + y, len(x), 0
    for _ in range(n):
        rnd.shuffle(pool)
        ge += statistics.mean(pool[:k]) - statistics.mean(pool[k:]) >= obs - 1e-12
    return (ge + 1) / (n + 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0] * len(ps), 0
    for rank, i in enumerate(order):
        run = max(run, min(1, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def pct(x):
    return "–" if x != x else f"{100 * x:.0f}%"


def main(main_dir):
    runs = load(main_dir)
    P = print
    P("# vuln-hunt: analysis\n")
    P(f"{len(runs)} runs. Runs without a FINDINGS.json: {sum(r['failed'] for r in runs)}.\n")

    P("## Planted vulnerabilities found, by tier\n")
    P("Mean share of each tier's vulnerabilities found per run (easy 3, medium 6, hard 9, very hard 5; 23 in all); "
      "**higher is better**. Runs: 10 per row.\n")
    P("| Arm | Easy | Medium | Hard | Very hard | Hard + very hard (of 14) | All (of 23) |")
    P("| --- | --- | --- | --- | --- | --- | --- |")
    for a, m, name in ARMS:
        rs = sel(runs, a, m)
        if not rs:
            continue
        cells = []
        for t in TIERS:
            ids = [v for v in V if V[v]["tier"] == t]
            cells.append(pct(statistics.mean(len(r["found"] & set(ids)) / len(ids) for r in rs)))
        hv = statistics.mean(len(r["found"] & set(HARD)) for r in rs)
        al = statistics.mean(len(r["found"]) for r in rs)
        P(f"| {name} | {' | '.join(cells)} | {hv:.1f} | {al:.1f} |")

    P("\n## Each vulnerability: share of runs that found it\n")
    P("Out of 10 runs per arm; **higher is better**.\n")
    P("| ID | OWASP | Tier | " + " | ".join(n.split(". ")[0] + (" Q" if m == "qwen" else "") for a, m, n in ARMS) + " |")
    P("| --- | --- | --- | " + " | ".join("---" for _ in ARMS) + " |")
    for vid, v in V.items():
        P(f"| {vid} | {v['owasp']} | {v['tier']} | " + " | ".join(pct(rate(sel(runs, a, m), vid)) for a, m, _ in ARMS) + " |")

    P("\n## By OWASP Top 10:2025 category\n")
    P("Mean share of the category's planted vulnerabilities found per run; **higher is better**.\n")
    P("| Category | " + " | ".join(n.split(". ")[0] + (" Q" if m == "qwen" else "") for a, m, n in ARMS) + " |")
    P("| --- | " + " | ".join("---" for _ in ARMS) + " |")
    for cat, cname in OWASP.items():
        ids = {v for v in V if V[v]["owasp"] == cat}
        cells = []
        for a, m, _ in ARMS:
            rs = sel(runs, a, m)
            cells.append(pct(statistics.mean(len(r["found"] & ids) / len(ids) for r in rs)) if rs else "–")
        P(f"| {cat} {cname} | " + " | ".join(cells) + " |")

    P("\n## Findings and false alarms\n")
    P("Per run (mean). Matched: findings that identify a planted vulnerability. Duplicates: extra findings for a "
      "vulnerability already matched. Decoys flagged and wrong findings are false alarms (**lower is better**); "
      "real issues outside the key are listed separately. Precision: matched / (findings - outside the key); "
      "**higher is better**.\n")
    P("| Arm | Findings | Matched | Duplicates | Real, outside the key | Decoys flagged | Wrong | Precision |")
    P("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for a, m, name in ARMS:
        rs = sel(runs, a, m)
        if not rs:
            continue
        pr = [r["precision"] for r in rs if r["precision"] is not None]
        P(f"| {name} | {statistics.mean(r['findings'] for r in rs):.1f} | {statistics.mean(r['matched'] for r in rs):.1f} "
          f"| {statistics.mean(r['dups'] for r in rs):.1f} | {statistics.mean(r['other'] for r in rs):.1f} "
          f"| {sum(r['decoys'] for r in rs)} in all | {sum(r['wrong'] for r in rs)} in all "
          f"| {pct(statistics.mean(pr)) if pr else '–'} |")

    P("\n## Cost and time\n")
    P("Per run (mean); cost at the model's list price (the same for Codex and OpenRouter's gpt-5.6-luna); "
      "**lower is better**. Qwen's price rises above 32k-token prompts; this uses the base price, so Qwen's cost is "
      "an underestimate.\n")
    P("| Arm | Cost | Median time | Tokens (input + output) | Total cost |")
    P("| --- | --- | --- | --- | --- |")
    for a, m, name in ARMS:
        rs = sel(runs, a, m)
        if not rs:
            continue
        P(f"| {name} | ${statistics.mean(r['cost'] for r in rs):.3f} | {statistics.median(r['seconds'] for r in rs):.0f} s "
          f"| {statistics.mean(r['tokens'] for r in rs) / 1000:.0f}k | ${sum(r['cost'] for r in rs):.2f} |")
    P(f"\nTotal: ${sum(r['cost'] for r in runs):.2f}.\n")

    for a, m, name in [("D", "luna", "D. Strands swarm"), ("C", "luna", "C. Strands team"), ("C", "qwen", "C. Strands team, Qwen")]:
        rs = sel(runs, a, m)
        if rs:
            agents = collections.Counter(a for r in rs for a in set(r["handoffs"] or []))
            P(f"**{name}:** statuses {dict(collections.Counter(str(r['status']) for r in rs))}; agents run per run "
              f"(– = run failed): {[len(set(r['handoffs'])) if r['handoffs'] else '–' for r in rs]}; "
              f"runs in which each agent ran: {dict(sorted(agents.items()))}.\n")

    P("## Hypotheses (Luna)\n")
    P("H1, H2, H4: mean difference in the per-vulnerability detection rate over the 14 hard and very-hard "
      "vulnerabilities (percentage points), exact one-sided sign-flip test, bootstrap 95% interval. H3: difference in "
      "mean precision, one-sided permutation test. Holm over H1-H4.\n")
    tests = []
    for h, x, y in [("H1: B > A", "B", "A"), ("H2: C > B", "C", "B"), ("H4: A2 > A", "A2", "A")]:
        diffs = [rate(sel(runs, x, "luna"), v) - rate(sel(runs, y, "luna"), v) for v in HARD]
        tests.append((h, 100 * statistics.mean(diffs), tuple(100 * b for b in boot(diffs)), signflip(diffs)))
    xb = [r["precision"] for r in sel(runs, "B", "luna") if r["precision"] is not None]
    xa = [r["precision"] for r in sel(runs, "A", "luna") if r["precision"] is not None]
    tests.insert(2, ("H3: precision B > A", 100 * (statistics.mean(xb) - statistics.mean(xa)), None, perm_runs(xb, xa)))
    adj = holm([t[3] for t in tests])
    P("| Hypothesis | Difference | 95% interval | p | Holm p |")
    P("| --- | --- | --- | --- | --- |")
    for (h, d, ci, p), ap in zip(tests, adj):
        P(f"| {h} | {d:+.1f} | {'–' if ci is None else f'{ci[0]:+.1f} to {ci[1]:+.1f}'} | {p:.4f} | {ap:.4f} |")
    diffs = [rate(sel(runs, "A2", "luna"), v) - rate(sel(runs, "B", "luna"), v) for v in HARD]
    lo, hi = boot(diffs)
    P(f"\nDescriptive, A2 - B (same instructions and model, Codex against Strands): {100 * statistics.mean(diffs):+.1f} "
      f"points (95% interval {100 * lo:+.1f} to {100 * hi:+.1f}).")
    for x, y in [("D", "C")]:
        diffs = [rate(sel(runs, x, "luna"), v) - rate(sel(runs, y, "luna"), v) for v in HARD]
        lo, hi = boot(diffs)
        P(f"Descriptive, D - C (swarm against Graph team): {100 * statistics.mean(diffs):+.1f} points "
          f"(95% interval {100 * lo:+.1f} to {100 * hi:+.1f}).")


if __name__ == "__main__":
    main(sys.argv[1])
