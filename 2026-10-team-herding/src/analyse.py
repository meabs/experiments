"""Scores every agent call against evidence-manipulation's hidden ground truth and builds the arms (README, "Arms" and
"Analysis"). Prints markdown. Deterministic.

Arms, per case and repeat:
  A  one Luna agent                        solo member 1
  B  three independent Luna agents, vote   majority of solo members 1-3
  C  three Luna agents after peer review   majority of revise members 1-3
  E  one Luna agent, token-matched         recheck pass 4 (the last pass)
  F  Sol reviewing C's three assessments   sol_review
  G  Sol on its own                        sol_solo
A majority needs 2 of 3 valid votes for the same decision; otherwise the arm has no decision, which counts as wrong.
Tests: the unit is the case. Per-case value = the number of correct repeats (0..reps). Exact sign-flip test over the 21
falsified cases (signflip_dp, as evidence-manipulation), bootstrap 95% CI over cases (test-skill's boot: 10,000 resamples,
seed 1), Holm over H1-H5. Prices: list, $ per million tokens (README, "Cost").
Usage: python3 -I src/analyse.py <out dir>
"""
import ast, collections, hashlib, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); X = os.path.dirname(ROOT)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(X, "2026-10-skills-impact", "scripts"))
from signflip_dp import signflip_exact, check  # noqa: E402
from stats import holm  # noqa: E402

src = open(os.path.join(X, "2026-10-test-skill", "scripts", "analyse.py")).read()
tree = ast.parse(src)
tree.body = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)) or
             (isinstance(n, ast.FunctionDef) and n.name in ("signflip_p", "boot"))]
ns = {"__file__": os.path.join(X, "2026-10-test-skill", "scripts", "analyse.py")}
exec(compile(tree, "test-skill analyse.py", "exec"), ns)
boot = ns["boot"]
check(ns["signflip_p"])

PRICE = {"gpt-5.6-luna": (0.20, 0.02, 1.20), "gpt-5.6-sol": (4.00, 0.40, 20.00)}  # input, cached input, output
EM = os.path.join(X, "2026-10-evidence-manipulation")
CASES = json.load(open(os.path.join(ROOT, "cases.json")))
for f, h in CASES["source"].items():
    assert hashlib.sha256(open(os.path.join(EM, f), "rb").read()).hexdigest() == h, f"{f} changed since cases.json"
H = json.load(open(os.path.join(EM, "scenarios", "ground_truth.json")))
D = sys.argv[1]
CALLS = [json.loads(l) for l in open(os.path.join(D, "calls.jsonl"))]
BY = {(c["case"], c["rep"], c["stage"], c["member"]): c for c in CALLS}
ARMS = {"A": "One Luna agent", "B": "Three Luna agents, independent vote", "C": "Three Luna agents after peer review",
        "E": "One Luna agent, token-matched (4 passes)", "F": "Sol reviews the team (C)", "G": "Sol alone"}


def cost(c):
    pi, pc, po = PRICE[c["model"]]
    u = c["usage"]
    return ((u["input_tokens"] - u["cached_input_tokens"]) * pi + u["cached_input_tokens"] * pc + u["output_tokens"] * po) / 1e6


def dec(c):
    return c["final"]["decision"] if c and c.get("final") else None


def majority(ds):
    n = collections.Counter(d for d in ds if d)
    top = n.most_common(1)
    return top[0][0] if top and top[0][1] >= 2 else None


def confident(c):
    f = (c or {}).get("final") or {}
    return f.get("uncertainty") == "low" and f.get("suspected_manipulation") is not True


def arms(case, rep):
    g = lambda s, m: BY.get((case, rep, s, m))
    solo = [g("solo", m) for m in (1, 2, 3)]
    rev = [g("revise", m) for m in (1, 2, 3)]
    rec = [g("recheck", m) for m in (1, 2, 3, 4)]
    fr, fs = g("sol_review", 1), g("sol_solo", 1)
    if not all(solo + rev + rec + [fr, fs]):
        return None
    return dict(
        A=dict(decision=dec(solo[0]), calls=[solo[0]], confident=confident(solo[0])),
        B=dict(decision=majority([dec(c) for c in solo]), calls=solo, members=[dec(c) for c in solo],
               confident=all(confident(c) for c in solo)),
        C=dict(decision=majority([dec(c) for c in rev]), calls=solo + rev, members=[dec(c) for c in rev],
               confident=all(confident(c) for c in rev)),
        E=dict(decision=dec(rec[3]), calls=rec, confident=confident(rec[3]), first=dec(rec[0])),
        F=dict(decision=dec(fr), calls=solo + rev + [fr], confident=confident(fr)),
        G=dict(decision=dec(fs), calls=[fs], confident=confident(fs)))


case_info = {c["case"]: c for c in CASES["cases"]}
reps = sorted({c["rep"] for c in CALLS})
R = {}  # (case, rep) -> arms
for case in sorted({c["case"] for c in CALLS}):
    for k in reps:
        a = arms(case, k)
        if a:
            truth = H[case_info[case]["scenario"]]["truth"]
            for v in a.values():
                v["correct"] = v["decision"] == truth
                v["usd"] = sum(cost(c) for c in v["calls"])
                v["tokens"] = sum(c["usage"]["input_tokens"] + c["usage"]["output_tokens"] for c in v["calls"])
            R[(case, k)] = (truth, a)

print(f"# Analysis of {os.path.basename(os.path.abspath(D))}\n")
print(f"{len(CALLS)} agent calls; {len(R)} complete case-repeats. Calls without a valid assessment: "
      f"{sum(1 for c in CALLS if not c['final'])}. Non-zero exit codes: {sum(1 for c in CALLS if c['returncode'] != 0)}.\n")

for variant, label in (("falsified", "one false fact (the 21 observable scenarios)"), ("clean", "clean evidence (9 scenarios)")):
    keys = [k for k in R if case_info[k[0]]["variant"] == variant]
    if not keys:
        continue
    print(f"## Correct decisions, {label}\n")
    print("Correct decisions out of case-repeats (higher is better). Confident wrong: wrong, uncertainty \"low\" and no "
          "suspected manipulation (for B and C: all three members; lower is better). Mean cost per case-repeat at list "
          "prices, including every call the arm needs (lower is better).\n")
    print("| Arm | Correct (higher is better) | Confident wrong (lower is better) | Mean tokens | Mean cost, $ (lower is better) |")
    print("| --- | --- | --- | --- | --- |")
    for a, name in ARMS.items():
        v = [R[k][1][a] for k in keys]
        print(f"| {a}. {name} | {sum(x['correct'] for x in v)}/{len(v)} | "
              f"{sum(1 for x in v if not x['correct'] and x['confident'])}/{len(v)} | "
              f"{st.mean(x['tokens'] for x in v):,.0f} | {st.mean(x['usd'] for x in v):.4f} |")
    print()

F = sorted(k for k in R if case_info[k[0]]["variant"] == "falsified")
if F:
    print("## Correlated errors and herding (falsified cases)\n")
    solo_wrong = [[d != R[k][0] for d in R[k][1]["B"]["members"]] for k in F]
    p = st.mean(x for t in solo_wrong for x in t)
    allw = sum(all(t) for t in solo_wrong)
    print(f"- Independent agents (B): single-agent error rate {p:.2f}. All three wrong in {allw}/{len(F)} triples; "
          f"if errors were independent, expected {p ** 3 * len(F):.1f}.")
    revw = sum(all(d != R[k][0] for d in R[k][1]["C"]["members"]) for k in F)
    print(f"- After peer review (C): all three wrong in {revw}/{len(F)} triples.")
    flips = collections.Counter()
    for k in F:
        for before, after in zip(R[k][1]["B"]["members"], R[k][1]["C"]["members"]):
            flips[(before == R[k][0], after == R[k][0])] += 1
    print(f"- Member answers after peer review: right to wrong {flips[(True, False)]}, wrong to right {flips[(False, True)]}, "
          f"unchanged right {flips[(True, True)]}, unchanged wrong {flips[(False, False)]}.")
    over = [(R[k][1]["F"]["decision"] != R[k][1]["C"]["decision"], R[k][1]["F"]["correct"]) for k in F]
    print(f"- Sol overruled the team in {sum(o for o, _ in over)}/{len(F)}; right when overruling: "
          f"{sum(1 for o, c in over if o and c)}; Sol agreed with a wrong team: "
          f"{sum(1 for k in F if R[k][1]['F']['decision'] == R[k][1]['C']['decision'] and not R[k][1]['C']['correct'])}.")
    e1 = sum(R[k][1]["E"]["first"] == R[k][0] for k in F)
    print(f"- Token-matched agent (E): first pass right {e1}/{len(F)}, after four passes {sum(R[k][1]['E']['correct'] for k in F)}/{len(F)}.\n")

    print("## Hypotheses (falsified cases; unit = case)\n")
    print("Per case: correct repeats in one arm minus the other. Positive means the first arm got more right.\n")
    cases = sorted({k[0] for k in F})
    def per(a):
        return {c: sum(R[(c, k)][1][a]["correct"] for k in reps if (c, k) in R) for c in cases}
    def unan(a):
        return {c: sum(all(d != R[(c, k)][0] for d in R[(c, k)][1][a]["members"]) for k in reps if (c, k) in R) for c in cases}
    HY = [("H1", "B − A: an independent vote of three vs one agent", per("B"), per("A"), True),
          ("H2", "C − B: all three wrong, after peer review vs independent (one-sided, more)", unan("C"), unan("B"), False),
          ("H3", "C − E: peer review vs one token-matched agent", per("C"), per("E"), True),
          ("H4", "F − C: Sol's final review vs the team without it", per("F"), per("C"), True),
          ("H5", "F − G: Sol shown the team's answers vs Sol alone", per("F"), per("G"), True)]
    rows, ps = [], []
    for hid, label, x, y, two in HY:
        d = [x[c] - y[c] for c in cases]
        pval = signflip_exact(d, two_sided=two)
        lo, hi = boot([v / len(reps) for v in d]) if len(d) > 1 else (0, 0)
        rows.append((hid, label, sum(v > 0 for v in d), sum(v == 0 for v in d), sum(v < 0 for v in d),
                     st.mean(d) / len(reps), lo, hi))
        ps.append(pval)
    print("| # | comparison | cases + / 0 / − | mean difference per case-repeat (95% CI) | Holm p |")
    print("| --- | --- | --- | --- | --- |")
    for (hid, label, a, z, b, m, lo, hi), p_ in zip(rows, holm(ps)):
        print(f"| {hid} | {label} | {a} / {z} / {b} | {m:+.2f} ({lo:+.2f} to {hi:+.2f}) | {p_:.3g} |")
    print()

print("## Cost\n")
by = collections.defaultdict(lambda: [0, 0.0, 0.0])
for c in CALLS:
    by[(c["model"], c["stage"])][0] += 1
    by[(c["model"], c["stage"])][1] += cost(c)
    by[(c["model"], c["stage"])][2] += c["seconds"]
print("| Model | Stage | Calls | Total $ at list price | Median seconds per call |")
print("| --- | --- | --- | --- | --- |")
for (m, s), (n, usd, _) in sorted(by.items()):
    secs = st.median(c["seconds"] for c in CALLS if c["model"] == m and c["stage"] == s)
    print(f"| {m} | {s} | {n} | {usd:.2f} | {secs:.0f} |")
print(f"\nTotal: ${sum(cost(c) for c in CALLS):.2f}.")
