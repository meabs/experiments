"""Analysis for diff-judge, fixed before the runs (README, "Hypotheses and analysis").

Unit: the task (12). Per task, model and arm: catch rate (failing items judged FAIL, of 4), accept rate (passing items
judged PASS, of 4), balanced accuracy (their mean). A reply without a verdict counts as wrong. Tests: exact sign-flip
over tasks (test-skill's signflip_p), bootstrap 95% CI over tasks, 10,000 resamples, seed 1 (test-skill's boot), Holm
over H1-H4 (stats.holm). Per-task quantities are kept in whole units (eighths or quarters) so the sign-flip is exact.
Usage: python3 -I analyse.py <results stage dir, e.g. results/main> > results/analysis.md
"""
import ast, glob, json, os, statistics as st, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE); X = os.path.dirname(N)
sys.path.insert(0, os.path.join(X, "2026-10-skills-impact", "scripts"))
from stats import holm  # noqa: E402

src = open(os.path.join(X, "2026-10-test-skill", "scripts", "analyse.py")).read()
tree = ast.parse(src)
tree.body = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)) or
             (isinstance(n, ast.FunctionDef) and n.name in ("signflip_p", "boot"))]
ns = {"__file__": os.path.join(X, "2026-10-test-skill", "scripts", "analyse.py")}
exec(compile(tree, "test-skill analyse.py", "exec"), ns)
signflip_p, boot = ns["signflip_p"], ns["boot"]

D = sys.argv[1]
J = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(D, "*", "*", "*", "judgement.json")))]
for f, j in zip(sorted(glob.glob(os.path.join(D, "*", "*", "*", "judgement.json"))), J):
    j["group"] = f.split(os.sep)[-4]  # local, hosted, local-retest
M = [j for j in J if j["group"] in ("local", "hosted")]
R = [j for j in J if j["group"] == "local-retest"]
MODELS = [m for m in ("local", "hosted") if any(j["group"] == m for j in M)]
ARMS = ["diff", "claim", "hedge"]
tasks = sorted({j["task"] for j in M})
cell = defaultdict(list)
for j in M:
    cell[(j["group"], j["arm"], j["task"])].append(j)


def caught(m, a, t):
    return sum(j["truth"] == "FAIL" and j["verdict"] == "FAIL" for j in cell[(m, a, t)])


def accepted(m, a, t):
    return sum(j["truth"] == "PASS" and j["verdict"] == "PASS" for j in cell[(m, a, t)])


def nfail(m, a, t):
    return sum(j["truth"] == "FAIL" for j in cell[(m, a, t)])


def agent_flagged(t):
    """Failing items of task t whose agent did not claim success (the agents' own catch), from the local J1 cell's items."""
    items = {j["item"]: j for j in M if j["task"] == t and j["truth"] == "FAIL"}
    return sum(j["agent_claim"] != "passed" for j in items.values())


def stats(d, scale, two_sided):
    rate = [x / scale for x in d]
    return st.mean(rate), boot(rate), signflip_p(d, two_sided)


def bsw(d):
    return f"{sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)}"


def pts(m, lo, hi):
    return f"{m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f})"


def ba_units(m, a, t):  # balanced accuracy - 0.5, in eighths
    return caught(m, a, t) + accepted(m, a, t) - 4


print(f"# diff-judge: analysis\n\n{len(M)} judgements ({dict(Counter((j['group'], j['arm']) for j in M))}), "
      f"{len(R)} repeated; {len(tasks)} tasks. Replies without a verdict: "
      f"{dict(Counter(j['group'] for j in M if j['verdict'] is None))}; timeouts: {sum(bool(j['timed_out']) for j in M)}.\n")
print("## Totals\n")
print("| model | arm | caught (failing judged FAIL) | accepted (passing judged PASS) | balanced accuracy | no verdict |")
print("| --- | --- | --- | --- | --- | --- |")
for m in MODELS:
    for a in ARMS:
        js = [j for j in M if j["group"] == m and j["arm"] == a]
        if not js:
            continue
        c = sum(caught(m, a, t) for t in tasks); f = sum(j["truth"] == "FAIL" for j in js)
        p = sum(accepted(m, a, t) for t in tasks); q = len(js) - f
        print(f"| {m} | {a} | {c}/{f} | {p}/{q} | {(c / f + p / q) / 2:.3f} | {sum(j['verdict'] is None for j in js)} |")
fa = [j for j in M if j["group"] == MODELS[0] and j["arm"] == "diff" and j["truth"] == "FAIL"]
print(f"\nThe agents' own reports flagged {sum(j['agent_claim'] != 'passed' for j in fa)} of these {len(fa)} failing changes "
      f"(claimed anything other than 'passed').\n")

print("## Hypotheses (preregistered)\n")
print("| # | comparison | tasks better / same / worse | mean per-task effect (95% CI) | p | Holm p |\n| --- | --- | --- | --- | --- | --- |")
H = []
if "local" in MODELS:
    H.append(("H1", "local, diff: balanced accuracy vs 0.5", [ba_units("local", "diff", t) for t in tasks], 8, False))
    H.append(("H2", "local: catch rate, diff vs claim", [caught("local", "diff", t) - caught("local", "claim", t) for t in tasks], 4, False))
    H.append(("H3", "local, diff: catch rate vs the agents' own reports", [caught("local", "diff", t) - agent_flagged(t) for t in tasks], 4, False))
if "local" in MODELS and "hosted" in MODELS:
    H.append(("H4", "diff: balanced accuracy, local vs hosted",
              [ba_units("local", "diff", t) - ba_units("hosted", "diff", t) for t in tasks], 8, True))
res = [stats(d, s, two) for _, _, d, s, two in H]
adj = holm([r[2] for r in res]) if H else []
for (h, name, d, s, two), (m, (lo, hi), p), ap in zip(H, res, adj):
    print(f"| {h} | {name} | {bsw(d)} | {pts(m, lo, hi)} | {p:.3f}{' (two-sided)' if two else ''} | {ap:.3f} |")

print("\n## Secondary (two-sided, unadjusted)\n")
print("| comparison | tasks better / same / worse | mean per-task effect (95% CI) | p |\n| --- | --- | --- | --- |")
sec = []
if "hosted" in MODELS:
    sec += [("hosted, diff: balanced accuracy vs 0.5", [ba_units("hosted", "diff", t) for t in tasks], 8),
            ("hosted: catch rate, diff vs claim", [caught("hosted", "diff", t) - caught("hosted", "claim", t) for t in tasks], 4),
            ("hosted, diff: catch rate vs the agents' own reports", [caught("hosted", "diff", t) - agent_flagged(t) for t in tasks], 4)]
for m in MODELS:
    sec += [(f"{m}: catch rate, hedge vs claim", [caught(m, "hedge", t) - caught(m, "claim", t) for t in tasks], 4),
            (f"{m}: accept rate, hedge vs claim", [accepted(m, "hedge", t) - accepted(m, "claim", t) for t in tasks], 4),
            (f"{m}: accept rate, diff vs claim", [accepted(m, "diff", t) - accepted(m, "claim", t) for t in tasks], 4)]
if "local" in MODELS and "hosted" in MODELS:
    for a in ARMS:
        sec += [(f"{a}: catch rate, local vs hosted", [caught("local", a, t) - caught("hosted", a, t) for t in tasks], 4),
                (f"{a}: accept rate, local vs hosted", [accepted("local", a, t) - accepted("hosted", a, t) for t in tasks], 4)]
        if a != "diff":
            sec.append((f"{a}: balanced accuracy, local vs hosted", [ba_units("local", a, t) - ba_units("hosted", a, t) for t in tasks], 8))
for name, d, s in sec:
    m, (lo, hi), p = stats(d, s, True)
    print(f"| {name} | {bsw(d)} | {pts(m, lo, hi)} | {p:.3f} |")

print("\n## Per task (caught of 4 / accepted of 4)\n")
cols = [(m, a) for m in MODELS for a in ARMS]
print("| task | " + " | ".join(f"{m} {a}" for m, a in cols) + " |\n| --- |" + " --- |" * len(cols))
for t in tasks:
    print(f"| {t} | " + " | ".join(f"{caught(m, a, t)} / {accepted(m, a, t)}" for m, a in cols) + " |")

print("\n## By failure kind (failing items judged FAIL)\n")
kinds = sorted({j["kind"] for j in M if j["truth"] == "FAIL"})
print("| model | arm | " + " | ".join(kinds) + " |\n| --- | --- |" + " --- |" * len(kinds))
for m in MODELS:
    for a in ARMS:
        js = [j for j in M if j["group"] == m and j["arm"] == a and j["truth"] == "FAIL"]
        print(f"| {m} | {a} | " + " | ".join(f"{sum(j['verdict'] == 'FAIL' for j in js if j['kind'] == k)}/{sum(j['kind'] == k for j in js)}" for k in kinds) + " |")

print("\n## Confidence\n")
print("| model | arm | mean confidence when right | when wrong | accuracy at confidence >= 80 | below 80 |\n| --- | --- | --- | --- | --- | --- |")
for m in MODELS:
    for a in ARMS:
        js = [j for j in M if j["group"] == m and j["arm"] == a and j["confidence"] is not None]
        right = [j["confidence"] for j in js if j["correct"]]; wrong = [j["confidence"] for j in js if not j["correct"]]
        hi = [j for j in js if j["confidence"] >= 80]; lo = [j for j in js if j["confidence"] < 80]
        f = lambda xs: f"{st.mean(xs):.0f}" if xs else "-"  # noqa: E731
        g = lambda xs: f"{sum(bool(j['correct']) for j in xs)}/{len(xs)}" if xs else "-"  # noqa: E731
        print(f"| {m} | {a} | {f(right)} | {f(wrong)} | {g(hi)} | {g(lo)} |")

print("\n## Verdict by diff size (all arms)\n")
for m in MODELS:
    js = [j for j in M if j["group"] == m]
    med = st.median(j["diff_bytes"] for j in js)
    for lab, part in (("small (<= median)", [j for j in js if j["diff_bytes"] <= med]), ("large", [j for j in js if j["diff_bytes"] > med])):
        print(f"- {m}, {lab}: judged PASS {sum(j['verdict'] == 'PASS' for j in part)}/{len(part)}, correct {sum(bool(j['correct']) for j in part)}/{len(part)}"
              f" (truly passing {sum(j['truth'] == 'PASS' for j in part)}).")

if R:
    first = {j["item"]: j["verdict"] for j in M if j["group"] == "local" and j["arm"] == "diff"}
    agree = sum(first.get(j["item"]) == j["verdict"] for j in R)
    print(f"\n## Stability\n\nRepeated local judgements (arm diff): {agree}/{len(R)} gave the same verdict as the first time.")


def cost(u):
    i, c, o = u.get("input_tokens", 0), u.get("cached_input_tokens", 0), u.get("output_tokens", 0)
    return ((i - c) * 0.20 + c * 0.02 + o * 1.20) / 1e6


print("\n## Time, tokens and cost\n")
print("| model | judgements | median s | total h | mean input | mean cached | mean output | $ at list prices | tool calls attempted |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for m in MODELS:
    js = [j for j in M if j["group"] == m]
    u = lambda k: st.mean((j["usage"] or {}).get(k, 0) for j in js) / 1e3  # noqa: E731
    print(f"| {m} | {len(js)} | {st.median(j['seconds'] for j in js):.0f} | {sum(j['seconds'] for j in js) / 3600:.2f} | {u('input_tokens'):.1f}k | "
          f"{u('cached_input_tokens'):.1f}k | {u('output_tokens'):.2f}k | {sum(cost(j['usage'] or {}) for j in js):.2f}"
          f"{' (equivalent)' if m == 'local' else ''} | {sum(j['tool_calls'] for j in js)} |")
p = os.path.join(D, "power.csv")
if os.path.exists(p) and "local" in MODELS:
    import csv
    from datetime import datetime
    rows = [(float(a), float(b)) for a, b in list(csv.reader(open(p)))[1:]]
    tot = 0.0
    for j in [j for j in J if j["group"] in ("local", "local-retest")]:
        t0 = datetime.fromisoformat(j["started"]).timestamp(); seg = [r for r in rows if t0 <= r[0] <= t0 + j["seconds"]]
        tot += sum((b[0] - a[0]) * a[1] for a, b in zip(seg, seg[1:])) / 3600
    print(f"\nLocal energy (APU package power over each judgement): {tot:.0f} Wh, £{tot / 1000 * 0.25:.3f} at £0.25/kWh.")
