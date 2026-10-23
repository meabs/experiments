"""Analysis for benchmark-twins, fixed before the runs (README, "Hypotheses and analysis").

Unit: the item. Per item and model, each variant is right (1) or wrong (0); a reply with no answer is wrong. The per-item
difference (original minus twin) is -1, 0 or +1. Tests: exact sign-flip over items (signflip_dp.py, the same test as
test-skill's signflip_p, computed by convolution), bootstrap 95% CI over items, 10,000 resamples, seed 1 (test-skill's
boot), Holm over H1-H4 (stats.holm).
Usage: python3 -I analyse.py <results stage dir, e.g. results/main> > results/analysis.md
"""
import ast, glob, json, os, statistics as st, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE); X = os.path.dirname(N)
sys.path.insert(0, os.path.join(X, "2026-10-skills-impact", "scripts")); sys.path.insert(0, HERE)
from stats import holm  # noqa: E402
from signflip_dp import signflip_exact, check  # noqa: E402

src = open(os.path.join(X, "2026-10-test-skill", "scripts", "analyse.py")).read()
tree = ast.parse(src)
tree.body = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)) or
             (isinstance(n, ast.FunctionDef) and n.name in ("signflip_p", "boot"))]
ns = {"__file__": os.path.join(X, "2026-10-test-skill", "scripts", "analyse.py")}
exec(compile(tree, "test-skill analyse.py", "exec"), ns)
boot = ns["boot"]
check(ns["signflip_p"])

D = sys.argv[1]
R = {}
for f in sorted(glob.glob(os.path.join(D, "*", "*", "*", "*", "result.json"))):
    model, bench, var, idx = f.split(os.sep)[-5:-1]
    R[(model, bench, var, int(idx))] = json.load(open(f))
MODELS = [m for m in ("local", "hosted") if any(k[0] == m for k in R)]
VARS = {"gsm8k": ["orig", "numbers", "names", "both"], "humaneval": ["orig", "renamed"]}


def right(m, b, v, i):
    return int(bool(R[(m, b, v, i)]["correct"]))


def items(m, b, v, w):
    """Items with both variants v and w answered by model m."""
    return sorted(i for (mm, bb, vv, i) in R if (mm, bb, vv) == (m, b, v) and (m, b, w, i) in R)


def diffs(m, b, w):
    return [right(m, b, "orig", i) - right(m, b, w, i) for i in items(m, b, "orig", w)]


def pts(m, lo, hi):
    return f"{m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f})"


def row(d, two):
    m = st.mean(d) if d else 0.0
    lo, hi = boot(d) if d else (0.0, 0.0)
    return m, lo, hi, signflip_exact(d, two)


def bsw(d):
    return f"{sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)}"


print("# Benchmark twins: analysis\n")
print(f"Answers: {len(R)}; models: {', '.join(MODELS)}.\n")
print("## Accuracy\n\n| model | benchmark | variant | right | no answer | timeouts |\n| --- | --- | --- | --- | --- | --- |")
for m in MODELS:
    for b, vs in VARS.items():
        for v in vs:
            rs = [r for k, r in R.items() if k[:3] == (m, b, v)]
            if rs:
                print(f"| {m} | {b} | {v} | {sum(bool(r['correct']) for r in rs)}/{len(rs)} ({sum(bool(r['correct']) for r in rs) / len(rs):.1%}) | "
                      f"{sum(r['answer'] is None for r in rs)} | {sum(bool(r['timed_out']) for r in rs)} |")

print("\n## Hypotheses (preregistered)\n")
print("Effect: accuracy on the original minus accuracy on the twin, over items with both. Positive means the twin is harder.\n")
print("| # | comparison | items orig right only / same / twin right only | mean effect (95% CI) | p | Holm p |\n| --- | --- | --- | --- | --- | --- |")
H = []
if "local" in MODELS:
    H += [("H1", "local, GSM8K: original vs numbers twin", diffs("local", "gsm8k", "numbers"), False),
          ("H2", "local, GSM8K: original vs names twin", diffs("local", "gsm8k", "names"), False),
          ("H3", "local, HumanEval: original vs renamed twin", diffs("local", "humaneval", "renamed"), False)]
if "local" in MODELS and "hosted" in MODELS:
    both = [i for i in items("local", "gsm8k", "orig", "numbers") if i in set(items("hosted", "gsm8k", "orig", "numbers"))]
    H.append(("H4", "GSM8K numbers-twin drop, local vs hosted",
              [(right("local", "gsm8k", "orig", i) - right("local", "gsm8k", "numbers", i)) -
               (right("hosted", "gsm8k", "orig", i) - right("hosted", "gsm8k", "numbers", i)) for i in both], True))
res = [row(d, two) for _, _, d, two in H]
adj = holm([r[3] for r in res]) if H else []
for (h, name, d, two), (m, lo, hi, p), ap in zip(H, res, adj):
    print(f"| {h} | {name} | {bsw(d)} | {pts(m, lo, hi)} | {p:.4f}{' (two-sided)' if two else ''} | {ap:.4f} |")

print("\n## Secondary (two-sided, unadjusted)\n")
print("| comparison | items orig right only / same / twin right only | mean effect (95% CI) | p |\n| --- | --- | --- | --- |")
sec = []
if "hosted" in MODELS:
    sec += [("hosted, GSM8K: original vs numbers twin", diffs("hosted", "gsm8k", "numbers")),
            ("hosted, GSM8K: original vs names twin", diffs("hosted", "gsm8k", "names")),
            ("hosted, HumanEval: original vs renamed twin", diffs("hosted", "humaneval", "renamed"))]
for m in MODELS:
    sec.append((f"{m}, GSM8K: original vs both twin", diffs(m, "gsm8k", "both")))
for name, d in sec:
    if d:
        m, lo, hi, p = row(d, True)
        print(f"| {name} | {bsw(d)} | {pts(m, lo, hi)} | {p:.4f} |")

print("\n## GSM8K numbers twin by number of steps\n\n| model | steps | items | original right | twin right |\n| --- | --- | --- | --- | --- |")
for m in MODELS:
    by = defaultdict(list)
    for i in items(m, "gsm8k", "orig", "numbers"):
        s = R[(m, "gsm8k", "orig", i)]["steps"]
        by["2" if s <= 2 else "3" if s == 3 else "4+"].append(i)
    for s in ("2", "3", "4+"):
        js = by[s]
        if js:
            print(f"| {m} | {s} | {len(js)} | {sum(right(m, 'gsm8k', 'orig', i) for i in js)} | {sum(right(m, 'gsm8k', 'numbers', i) for i in js)} |")


def cost(u):
    i, c, o = u.get("input_tokens", 0), u.get("cached_input_tokens", 0), u.get("output_tokens", 0)
    return ((i - c) * 0.20 + c * 0.02 + o * 1.20) / 1e6


print("\n## Time, tokens and cost\n")
print("| model | benchmark | answers | median s | total h | mean input | mean cached | mean output | $ at list prices | tool calls attempted |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for m in MODELS:
    for b in VARS:
        js = [r for k, r in R.items() if k[:2] == (m, b)]
        if not js:
            continue
        u = lambda k: st.mean((j["usage"] or {}).get(k, 0) for j in js) / 1e3  # noqa: E731
        print(f"| {m} | {b} | {len(js)} | {st.median(j['seconds'] for j in js):.0f} | {sum(j['seconds'] for j in js) / 3600:.2f} | {u('input_tokens'):.1f}k | "
              f"{u('cached_input_tokens'):.1f}k | {u('output_tokens'):.2f}k | {sum(cost(j['usage'] or {}) for j in js):.2f}"
              f"{' (equivalent)' if m == 'local' else ''} | {sum(j['tool_calls'] for j in js)} |")
p = os.path.join(D, "power.csv")
if os.path.exists(p) and "local" in MODELS:
    import csv
    from datetime import datetime
    rows = [(float(a), float(b)) for a, b in list(csv.reader(open(p)))[1:]]
    tot = 0.0
    for j in [r for k, r in R.items() if k[0] == "local"]:
        t0 = datetime.fromisoformat(j["started"]).timestamp(); seg = [r for r in rows if t0 <= r[0] <= t0 + j["seconds"]]
        tot += sum((b[0] - a[0]) * a[1] for a, b in zip(seg, seg[1:])) / 3600
    print(f"\nLocal energy (APU package power over each answer): {tot:.0f} Wh, £{tot / 1000 * 0.25:.3f} at £0.25/kWh.")
