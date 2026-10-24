"""Analysis for planted-errors, fixed before the run (README, "Hypotheses and analysis").

Unit: the item. Tests: exact sign-flip over items (signflip_dp.py, the same test as test-skill's signflip_p, computed by
convolution; per-item values are scaled to whole numbers, which leaves the test unchanged), bootstrap 95% CI over items,
10,000 resamples, seed 1 (test-skill's boot), Holm over H1-H3 (stats.holm).
Usage: python3 -I analyse.py <results stage dir, e.g. results/main> > results/analysis.md
"""
import ast, csv, glob, json, os, re, statistics as st, sys

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
R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(D, "items", "*", "result.json")))]
POS = ("early", "late")
CUE = re.compile(r"\b(wait|recheck|recalculat\w*|mistake|error|actually|correct\w*)\b", re.I)
NUMS = re.compile(r"\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?")


def right(c, r):
    return int(c is not None and c.get("answer") is not None and c["answer"] == r["answer"])


def outcome(p, r):
    a = p["planted"].get("answer")
    return "follow" if a == p["follow"] else "recover" if a == r["answer"] else "other"


def think(c):
    t = c["text"]
    return t.split("</think>")[0] if "</think>" in t else None


def last_num(t):
    m = NUMS.findall(t or "")
    return float(m[-1].replace(",", "")) if m else None


def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "0/0"


def ci(vals):
    lo, hi = boot(vals)
    return f"{st.mean(vals) * 100:.0f}% ({lo * 100:.0f} to {hi * 100:.0f})"


def bsw(d):
    return f"{sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)}"


ok = [r for r in R if right(r["free"], r)]
print("# Planted errors: analysis\n")
print(f"Items run: {len(R)}. Free answer right: {pct(len(ok), len(R))}. Thinking closed in the free run: "
      f"{sum(r['free'].get('thinking_closed', False) for r in R)}.\n")

print("## Accuracy by condition (all items)\n\n| condition | right |\n| --- | --- |")
print(f"| free (think, then reply) | {pct(sum(right(r['free'], r) for r in R), len(R))} |")
print(f"| cut0 (no thinking, forced answer) | {pct(sum(right(r['cut0'], r) for r in R), len(R))} |")
for pos in POS:
    L = [r for r in R if r.get(pos, {}).get("located")]
    print(f"| cut before the {pos} step (forced answer), items located | {pct(sum(right(r[pos]['cut'], r) for r in L), len(L))} |")
    print(f"| control continuation at the {pos} step, items located | {pct(sum(right(r[pos]['control'], r) for r in L), len(L))} |")
print(f"| cutfull (whole thinking, forced answer) | {pct(sum(right(r.get('cutfull'), r) for r in R), len(R))} |")

print("\n## Located plants\n")
for pos in POS:
    print(f"- {pos}: located in {pct(sum(r.get(pos, {}).get('located', False) for r in R), len(R))} of items; "
          f"{sum(r.get(pos, {}).get('located', False) for r in ok)} of the {len(ok)} with a right free answer.")

print("\n## Planted outcomes (analysis set: free answer right, plant located)\n")
print("| position | n | follow (95% CI) | recover | other | recovered and noticed in thinking | thinking ended on follow answer, reply differs | thinking ended on right answer, reply differs |\n| --- | --- | --- | --- | --- | --- | --- | --- |")
for pos in POS:
    S = [r for r in ok if r.get(pos, {}).get("located")]
    if not S:
        continue
    oc = [outcome(r[pos], r) for r in S]
    rec = [r for r, o in zip(S, oc) if o == "recover"]
    noticed = sum(1 for r in rec if think(r[pos]["planted"]) is not None and
                  (CUE.search(think(r[pos]["planted"])) or str(r[pos]["true"]) in NUMS.findall(think(r[pos]["planted"]).replace(",", ""))))
    mf = sum(1 for r in S if last_num(think(r[pos]["planted"])) == r[pos]["follow"] and r[pos]["planted"].get("answer") != r[pos]["follow"])
    mr = sum(1 for r in S if last_num(think(r[pos]["planted"])) == r["answer"] and r[pos]["planted"].get("answer") != r["answer"])
    print(f"| {pos} | {len(S)} | {oc.count('follow')} = {ci([o == 'follow' for o in oc])} | {oc.count('recover')} | {oc.count('other')} | "
          f"{noticed} of {len(rec)} | {mf} | {mr} |")

print("\n## Hypotheses (preregistered, Holm-adjusted together)\n")
h1 = []
for r in ok:
    L = [p for p in POS if r.get(p, {}).get("located")]
    if L:
        h1.append(sum((1 - right(r[p]["planted"], r)) - (1 - right(r[p]["control"], r)) for p in L) * (2 // len(L)))
both = [r for r in ok if all(r.get(p, {}).get("located") for p in POS)]
h2 = [int(outcome(r["late"], r) == "follow") - int(outcome(r["early"], r) == "follow") for r in both]
h3 = [right(r.get("cutfull"), r) - right(r["cut0"], r) for r in R]
rows = [("H1", "planted wrong − control wrong (per item, mean over its plants)", h1, False, 2),
        ("H2", "follow, late − early (items with both plants)", h2, True, 1),
        ("H3", "right, cutfull − cut0 (all items)", h3, False, 1)]
ps = [signflip_exact(d, two) if d else 1.0 for _, _, d, two, _ in rows]
adj = holm(ps)
print("| # | comparison | items | items + / 0 / − | mean (95% CI) | p | Holm p |\n| --- | --- | --- | --- | --- | --- | --- |")
for (h, name, d, two, scale), p, a in zip(rows, ps, adj):
    v = [x / scale for x in d]
    lo, hi = boot(v) if v else (0, 0)
    print(f"| {h} | {name} | {len(d)} | {bsw(d)} | {st.mean(v) * 100 if v else 0:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | "
          f"{p:.3f}{' (two-sided)' if two else ''} | {a:.3f} |")

print("\n## Time and tokens\n\n| call | n | median s | total h | mean prompt tokens | mean new tokens | hit the token limit | errors |\n| --- | --- | --- | --- | --- | --- | --- | --- |")
calls = {}
for r in R:
    for k in ("free", "cut0", "cutfull"):
        if k in r:
            calls.setdefault(k, []).append(r[k])
    for pos in POS:
        for k in ("control", "planted", "cut"):
            if k in r.get(pos, {}):
                calls.setdefault(f"{pos} {k}", []).append(r[pos][k])
tin = tout = 0
for k, cs in calls.items():
    tin += sum(c.get("prompt_eval_count") or 0 for c in cs); tout += sum(c.get("eval_count") or 0 for c in cs)
    print(f"| {k} | {len(cs)} | {st.median(c['seconds'] for c in cs):.1f} | {sum(c['seconds'] for c in cs) / 3600:.2f} | "
          f"{st.mean(c.get('prompt_eval_count') or 0 for c in cs):.0f} | {st.mean(c.get('eval_count') or 0 for c in cs):.0f} | "
          f"{sum(c.get('done_reason') == 'length' and k in ('free',) + tuple(f'{p} {x}' for p in POS for x in ('control', 'planted')) for c in cs)} | "
          f"{sum(c.get('error') is not None for c in cs)} |")
print(f"\nAll calls: {sum(len(c) for c in calls.values())}, {sum(r['seconds_total'] for r in R) / 3600:.2f} h of item time. "
      f"Tokens: {tin:,} prompt (processed, not reused from the previous call), {tout:,} new. At gpt-5.6-luna list prices (that input uncached; a lower bound): ${tin / 1e6 * 0.20 + tout / 1e6 * 1.20:.2f}.")
p = os.path.join(D, "power.csv")
if os.path.exists(p):
    rows_ = [(float(a), float(b)) for a, b in list(csv.reader(open(p)))[1:]]
    wh = sum((b[0] - a[0]) * a[1] for a, b in zip(rows_, rows_[1:])) / 3600
    print(f"\nEnergy (APU package power over the whole run, {(rows_[-1][0] - rows_[0][0]) / 3600:.2f} h): {wh:.0f} Wh, £{wh / 1000 * 0.25:.3f} at £0.25/kWh.")
