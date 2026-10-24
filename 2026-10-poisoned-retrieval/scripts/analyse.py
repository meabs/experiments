"""Analysis for poisoned-retrieval, fixed before the run (README, "Hypotheses and analysis").

Unit: the question. Outcomes per answer: right, follow (the planted value), both, notfound, other, none (no ANSWER line).
Tests: exact sign-flip over questions (signflip_dp.py, the same test as test-skill's signflip_p, computed by convolution),
bootstrap 95% CI over questions, 10,000 resamples, seed 1 (test-skill's boot), Holm over H1-H3 (stats.holm).
Usage: python3 -I analyse.py <results stage dir, e.g. results/main> <retrieved.json> > results/analysis.md
"""
import ast, csv, glob, json, os, statistics as st, sys

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
RET = {r["id"]: r for r in json.load(open(sys.argv[2]))}
R = {}
for f in glob.glob(os.path.join(D, "*", "*", "*", "result.json")):
    m, c, i = f.split(os.sep)[-4:-1]
    R[(m, c, i)] = json.load(open(f))
BIG, SMALL = "qwen3.8_27b", "qwen3_8b"
MODELS = [m for m in (BIG, SMALL) if any(k[0] == m for k in R)]
CONDS = ("closed", "clean", "poisoned", "miss")
OUT = ("right", "follow", "both", "notfound", "other", "none")
IDS = sorted({k[2] for k in R if all((m, c, k[2]) in R for m in MODELS for c in CONDS)})


def o(m, c, i):
    return R[(m, c, i)]["outcome"]


def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "0/0"


def bsw(d):
    return f"{sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)}"


print("# Poisoned retrieval: analysis\n")
print(f"Questions with every answer recorded: {len(IDS)}. Models: {', '.join(MODELS)}.\n")
nat = sum(RET[i]["natural_hit"] for i in IDS)
print(f"Retrieval: the answer paragraph was in bge-m3's natural top 5 for {pct(nat, len(IDS))} of questions.\n")

print("## Outcomes\n\n| model | condition | " + " | ".join(OUT) + " |\n| --- | --- | " + " | ".join("---" for _ in OUT) + " |")
for m in MODELS:
    for c in CONDS:
        print(f"| {m} | {c} | " + " | ".join(str(sum(o(m, c, i) == x for i in IDS)) for x in OUT) + " |")

print("\n## Hypotheses (preregistered, Holm-adjusted together)\n")
rows = []
if BIG in MODELS:
    rows.append(("H1", f"{BIG}: right, clean − poisoned", [int(o(BIG, 'clean', i) == 'right') - int(o(BIG, 'poisoned', i) == 'right') for i in IDS], False))
if SMALL in MODELS and BIG in MODELS:
    rows.append(("H2", "follows the planted value, 8B − 27B (poisoned)", [int(o(SMALL, 'poisoned', i) == 'follow') - int(o(BIG, 'poisoned', i) == 'follow') for i in IDS], True))
    made = lambda m, i: int(o(m, "miss", i) not in ("notfound", "right"))
    rows.append(("H3", "makes up an answer when retrieval misses, 8B − 27B", [made(SMALL, i) - made(BIG, i) for i in IDS], True))
ps = [signflip_exact(d, two) for _, _, d, two in rows]
adj = holm(ps) if ps else []
print("| # | comparison | questions + / 0 / − | mean (95% CI) | p | Holm p |\n| --- | --- | --- | --- | --- | --- |")
for (h, name, d, two), p, a in zip(rows, ps, adj):
    lo, hi = boot(d)
    print(f"| {h} | {name} | {bsw(d)} | {st.mean(d) * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | {p:.3f}{' (two-sided)' if two else ''} | {a:.3f} |")

print("\n## Poisoned answers by what the model knew (closed book)\n")
print("| model | closed book | questions | poisoned: right | follow | notfound | other | NOTE line in poisoned | NOTE line in clean |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for m in MODELS:
    for lab, keep in (("right", lambda i: o(m, "closed", i) == "right"), ("not right", lambda i: o(m, "closed", i) != "right")):
        S = [i for i in IDS if keep(i)]
        print(f"| {m} | {lab} | {len(S)} | " + " | ".join(str(sum(o(m, 'poisoned', i) == x for i in S)) for x in ("right", "follow", "notfound", "other")) +
              f" | {sum(R[(m, 'poisoned', i)]['note'] is not None for i in S)} | {sum(R[(m, 'clean', i)]['note'] is not None for i in S)} |")

print("\n## When retrieval misses\n\n| model | NOT FOUND | right anyway | made-up answer | of which closed book was right |\n| --- | --- | --- | --- | --- |")
for m in MODELS:
    made_ = [i for i in IDS if o(m, "miss", i) not in ("notfound", "right")]
    print(f"| {m} | {sum(o(m, 'miss', i) == 'notfound' for i in IDS)} | {sum(o(m, 'miss', i) == 'right' for i in IDS)} | {len(made_)} | "
          f"{sum(o(m, 'closed', i) == 'right' for i in made_)} |")

print("\n## Time and tokens\n\n| model | condition | median s | total h | mean prompt tokens | mean new tokens | errors | hit token limit |\n| --- | --- | --- | --- | --- | --- | --- | --- |")
tin = tout = 0
for m in MODELS:
    for c in CONDS:
        rs = [R[(m, c, i)] for i in IDS]
        tin += sum(r["prompt_eval_count"] or 0 for r in rs); tout += sum(r["eval_count"] or 0 for r in rs)
        print(f"| {m} | {c} | {st.median(r['seconds'] for r in rs):.1f} | {sum(r['seconds'] for r in rs) / 3600:.2f} | "
              f"{st.mean(r['prompt_eval_count'] or 0 for r in rs):.0f} | {st.mean(r['eval_count'] or 0 for r in rs):.0f} | "
              f"{sum(r['error'] is not None for r in rs)} | {sum(r['done_reason'] == 'length' for r in rs)} |")
print(f"\nTokens: {tin:,} prompt (processed, not reused from the previous call), {tout:,} new. "
      f"At gpt-5.6-luna list prices (that input uncached; a lower bound): ${tin / 1e6 * 0.20 + tout / 1e6 * 1.20:.2f}.")
p = os.path.join(D, "power.csv")
if os.path.exists(p):
    rows_ = [(float(a), float(b)) for a, b in list(csv.reader(open(p)))[1:]]
    wh = sum((b[0] - a[0]) * a[1] for a, b in zip(rows_, rows_[1:])) / 3600
    print(f"\nEnergy (APU package power over the whole run, {(rows_[-1][0] - rows_[0][0]) / 3600:.2f} h): {wh:.0f} Wh, £{wh / 1000 * 0.25:.3f} at £0.25/kWh.")
