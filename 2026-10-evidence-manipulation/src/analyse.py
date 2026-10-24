"""Analysis, fixed before the measured run (HYPOTHESES.md). One command regenerates it from the raw runs.

Unit: the scenario. For each scenario and condition, a measure is the mean over its seeds (so every run of a scenario
travels together). Paired differences are per scenario. Tests: exact sign-flip over scenarios (signflip_dp.py, the test
from test-skill computed by convolution; per-scenario means are scaled to whole numbers, which leaves the test unchanged),
bootstrap 95% CI over scenarios (test-skill's boot: 10,000 resamples, seed 1), Holm over H1, H2, H3a, H3b, H4.
Usage: python3 -I src/analyse.py <results dir, e.g. results/main> > <results dir>/analysis.md
       (also writes <results dir>/scores.jsonl, one scored line per run)
"""
import ast, collections, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); X = os.path.dirname(ROOT)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(X, "2026-10-skills-impact", "scripts"))
from score import score  # noqa: E402
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

D = sys.argv[1]
H = json.load(open(os.path.join(ROOT, "scenarios", "ground_truth.json")))
RUNS = [json.loads(l) for l in open(os.path.join(D, "runs.jsonl"))]
SC = [score(r, H) for r in RUNS]
with open(os.path.join(D, "scores.jsonl"), "w") as f:
    for s in SC:
        f.write(json.dumps(s) + "\n")
CONDS = ["clean", "falsified", "injection", "combined", "falsified_v", "injection_v", "combined_v"]
IDS = sorted(H)
by = collections.defaultdict(list)
for s in SC:
    by[(s["scenario"], s["condition"])].append(s)


def attack(s):
    return s["target_decision"] or s["target_action"]


def mean_of(i, c, f):
    v = [f(s) for s in by[(i, c)]]
    return st.mean(v) if v else None


def rate(c, f, ids=IDS):
    v = [f(s) for i in ids for s in by[(i, c)]]
    return sum(v), len(v)


def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "-"


print("# Evidence manipulation: analysis\n")
print(f"Runs: {len(RUNS)}. Scenarios: {len({s['scenario'] for s in SC})}. Valid final assessments: {sum(s['valid'] for s in SC)}. "
      f"Runs with a model error: {sum(s['errors'] > 0 for s in SC)}. Format retries: {sum(s['format_retry'] for s in SC)}. "
      f"Hit the tool-round limit: {sum(s['hit_round_limit'] for s in SC)}.\n")

COLS = [("correct", lambda s: s["correct"]), ("false negative", lambda s: s["false_negative"]),
        ("false positive", lambda s: s["false_positive"]), ("attack target reached", attack),
        ("inappropriate action", lambda s: s["inappropriate"]), ("of which attempted via tool", lambda s: s["inappropriate_attempt"]),
        ("deferred (request_investigation)", lambda s: s["deferred"]), ("flagged manipulation", lambda s: s["detected"]),
        ("used verify", lambda s: s["verify_used"]), ("ran the resolving check", lambda s: s["verify_relevant"]),
        ("confident error", lambda s: s["confident_error"]), ("decision/action inconsistent", lambda s: s["inconsistent"]),
        ("cited an id it never saw", lambda s: bool(s["bad_references"])), ("invented identifier", lambda s: bool(s["invented_ids"])),
        ("reasonable given evidence", lambda s: s["reasonable"]), ("invalid output", lambda s: not s["valid"])]
print("## Rates by condition (all runs)\n\n| measure | " + " | ".join(CONDS) + " |\n| --- |" + " --- |" * len(CONDS))
for name, f in COLS:
    print(f"| {name} | " + " | ".join(pct(*rate(c, f)) for c in CONDS) + " |")

for lab, sel in (("genuine threats", lambda i: H[i]["truth"] == "malicious"), ("benign activity", lambda i: H[i]["truth"] == "benign"),
                 ("observable manipulation", lambda i: H[i]["kind"] == "observable"), ("unresolvable manipulation", lambda i: H[i]["kind"] == "unresolvable")):
    ids = [i for i in IDS if sel(i)]
    print(f"\n### {lab} ({len(ids)} scenarios)\n\n| measure | " + " | ".join(CONDS) + " |\n| --- |" + " --- |" * len(CONDS))
    for name, f in COLS[:9]:
        print(f"| {name} | " + " | ".join(pct(*rate(c, f, ids)) for c in CONDS) + " |")


def diffs(a, b, f, ids=IDS):
    return [mean_of(i, a, f) - mean_of(i, b, f) for i in ids if mean_of(i, a, f) is not None and mean_of(i, b, f) is not None]


def scaled(d, k):
    return [round(x * k) for x in d]


wrong = lambda s: not s["correct"]
h4 = []
for i in IDS:
    v = [mean_of(i, c, wrong) - mean_of(i, c + "_v", wrong) for c in ("falsified", "injection", "combined")
         if mean_of(i, c, wrong) is not None and mean_of(i, c + "_v", wrong) is not None]
    if len(v) == 3:
        h4.append(st.mean(v))
tests = [("H1", "incorrect decision: falsified − clean", diffs("falsified", "clean", wrong), 3, False),
         ("H2", "inappropriate action: injection − clean", diffs("injection", "clean", lambda s: s["inappropriate"]), 3, False),
         ("H3a", "attack target reached: combined − falsified", diffs("combined", "falsified", attack), 3, True),
         ("H3b", "attack target reached: combined − injection", diffs("combined", "injection", attack), 3, True),
         ("H4", "incorrect decision: without − with verification (mean of the three manipulations)", h4, 9, False)]
ps = [signflip_exact(scaled(d, k), two) if d else 1.0 for _, _, d, k, two in tests]
adj = holm(ps)
print("\n## Hypotheses (preregistered; Holm over H1-H4)\n\nPer-scenario differences of per-scenario rates (mean over seeds).\n")
print("| # | comparison | scenarios + / 0 / − | mean difference (95% CI) | p | Holm p |\n| --- | --- | --- | --- | --- | --- |")
for (h, name, d, k, two), p, a in zip(tests, ps, adj):
    lo, hi = boot(d) if d else (0, 0)
    print(f"| {h} | {name} | {sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)} | "
          f"{st.mean(d) * 100 if d else 0:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | {p:.3f}{' (two-sided)' if two else ''} | {a:.3f} |")

inc = [s for s in SC if s["valid"] and not s["correct"]]
conf = [s for s in inc if s["confident_error"]]
per = [st.mean([s["confident_error"] for s in inc if s["scenario"] == i]) for i in IDS if any(s["scenario"] == i for s in inc)]
lo, hi = boot(per) if len(per) > 1 else (0, 0)
print(f"\n### H5 (descriptive)\n\nIncorrect valid decisions: {len(inc)}. Stated with uncertainty \"low\" and no suspected manipulation: "
      f"{pct(len(conf), len(inc))}. Mean per scenario with any incorrect decision: {st.mean(per) * 100 if per else 0:.0f}% "
      f"(95% CI {lo * 100:.0f} to {hi * 100:.0f}, {len(per)} scenarios).")
print("\n| condition | incorrect | confident | low | medium | high |\n| --- | --- | --- | --- | --- | --- |")
for c in CONDS:
    ic = [s for s in inc if s["condition"] == c]
    print(f"| {c} | {len(ic)} | {sum(s['confident_error'] for s in ic)} | " + " | ".join(str(sum(s['uncertainty'] == u for s in ic)) for u in ("low", "medium", "high")) + " |")

print("\n## Secondary (two-sided, unadjusted)\n\n| comparison | scenarios + / 0 / − | mean difference (95% CI) | p |\n| --- | --- | --- | --- |")
for name, a, b, f in (("incorrect: injection − clean", "injection", "clean", wrong), ("incorrect: combined − clean", "combined", "clean", wrong),
                      ("inappropriate action: falsified − clean", "falsified", "clean", lambda s: s["inappropriate"]),
                      ("inappropriate action: combined − clean", "combined", "clean", lambda s: s["inappropriate"]),
                      ("incorrect: falsified − falsified_v", "falsified", "falsified_v", wrong),
                      ("incorrect: injection − injection_v", "injection", "injection_v", wrong),
                      ("incorrect: combined − combined_v", "combined", "combined_v", wrong),
                      ("flagged: injection − clean", "injection", "clean", lambda s: s["detected"]),
                      ("flagged: falsified − clean", "falsified", "clean", lambda s: s["detected"])):
    d = diffs(a, b, f)
    lo, hi = boot(d)
    print(f"| {name} | {sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)} | {st.mean(d) * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | {signflip_exact(scaled(d, 3), True):.3f} |")

print("\n## Verification: did checking the right record help? (exploratory)\n\n| condition | runs | ran the resolving check | correct when it did | correct when it did not |\n| --- | --- | --- | --- | --- |")
for c in ("falsified_v", "injection_v", "combined_v"):
    rs = [s for s in SC if s["condition"] == c]
    y = [s for s in rs if s["verify_relevant"]]; n_ = [s for s in rs if not s["verify_relevant"]]
    print(f"| {c} | {len(rs)} | {len(y)} | {pct(sum(s['correct'] for s in y), len(y))} | {pct(sum(s['correct'] for s in n_), len(n_))} |")

print("\n## Time and tokens\n\n| condition | runs | median s | total h | mean prompt tokens | mean output tokens | mean tool rounds |\n| --- | --- | --- | --- | --- | --- | --- |")
rounds = {(r["scenario"], r["condition"], r["seed"]): r["rounds"] for r in RUNS}
for c in CONDS:
    rs = [s for s in SC if s["condition"] == c]
    if rs:
        print(f"| {c} | {len(rs)} | {st.median(s['seconds'] for s in rs):.0f} | {sum(s['seconds'] for s in rs) / 3600:.2f} | "
              f"{st.mean(s['prompt_tokens'] for s in rs):.0f} | {st.mean(s['output_tokens'] for s in rs):.0f} | "
              f"{st.mean(rounds[(s['scenario'], s['condition'], s['seed'])] for s in rs):.1f} |")
tin, tout = sum(s["prompt_tokens"] for s in SC), sum(s["output_tokens"] for s in SC)
print(f"\nTokens: {tin:,} prompt (processed, not reused from a previous call), {tout:,} output. "
      f"At gpt-5.6-luna list prices (that input uncached; a lower bound): ${tin / 1e6 * 0.20 + tout / 1e6 * 1.20:.2f}.")
p = os.path.join(D, "power.csv")
if os.path.exists(p):
    import csv
    rw = [(float(a), float(b)) for a, b in list(csv.reader(open(p)))[1:]]
    wh = sum((b[0] - a[0]) * a[1] for a, b in zip(rw, rw[1:])) / 3600
    print(f"\nEnergy (APU package power over the run, {(rw[-1][0] - rw[0][0]) / 3600:.2f} h): {wh:.0f} Wh, £{wh / 1000 * 0.25:.2f} at £0.25/kWh.")

print("\n## Incorrect decisions, for inspection and replay\n\n`python3 -I src/run.py <dir> --only <scenario>/<condition>/<seed>` replays one run; `src/show.py` prints its transcript.\n")
print("| scenario | condition | seed | truth | kind | decision | action | attempted | flagged | uncertainty |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for s in sorted(inc, key=lambda s: (s["scenario"], CONDS.index(s["condition"]), s["seed"])):
    print(f"| {s['scenario']} | {s['condition']} | {s['seed']} | {s['truth']} | {s['kind']} | {s['decision']} | {s['final_action']} | "
          f"{','.join(s['attempted_actions']) or '-'} | {s['detected']} | {s['uncertainty']} |")
