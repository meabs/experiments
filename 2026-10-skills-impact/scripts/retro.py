"""Retrospective and exploratory analysis of stage 1. Nothing here replaces the preregistered tests in analyse.py.

Inputs, all committed: results/runs.csv (from analyse.py), results/stage1/runs/*/run.json, results/stage1/bite.json
(original H4), results/retro/{mutation,process,audit}.json (from mutation.py, process.py, audit.py).
Usage: python3 -I retro.py > results/retro/analysis-retro.md
"""
import csv, json, os, statistics as st, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats import fisher_greater, fisher_two_sided, holm, newcombe, wilson  # noqa: E402

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(E, "results")
rows = list(csv.DictReader(open(os.path.join(R, "runs.csv"))))
for r in rows:
    r["key"] = f"{r['q']}/{r['arm']}/{r['agent']}/{r['rep']}"
    r["passed"] = r["passed"] == "True"
    r["skill_read"] = r["skill_read"] == "True"
    t = json.load(open(os.path.join(R, "stage1/runs", r["key"], "run.json")))["tokens"]
    r["tok"] = t
bite = json.load(open(os.path.join(R, "stage1/bite.json")))
mut = json.load(open(os.path.join(R, "retro/mutation.json")))
proc = json.load(open(os.path.join(R, "retro/process.json")))
audit = json.load(open(os.path.join(R, "retro/audit.json")))
ARMS = ["none", "placebo", "superpowers", "pocock", "pstack"]
AGENTS = ["codex", "cursor"]
TASKS = ["BUG", "CROSS", "FEAT"]


def sel(**kw):
    return [r for r in rows if all(r[k] in (v if isinstance(v, (list, tuple)) else [v]) for k, v in kw.items())]


def pct(x):
    return f"{x * 100:+.0f}" if x else "0"


def rd(x1, n1, x2, n2):
    d, lo, hi = newcombe(x1, n1, x2, n2)
    return f"{d * 100:+.0f} pts ({lo * 100:+.0f} to {hi * 100:+.0f})"


out = []
P = out.append

# 1. Preregistered family with effect sizes and Holm adjustment
P("## 1. Preregistered tests: effect sizes and multiple comparisons\n")
P("The tests and their raw p-values are exactly those in `analysis.md`. Added here: the difference in rates with a "
  "Newcombe 95% interval, and Holm-adjusted p-values across the nine preregistered tests (H1, H2, H7, three H4, three H5). "
  "H6 was descriptive. Test-first is reported under its new name, test-file-first.\n")
hard = ["BUG", "CROSS"]
fam = []


def add(label, name, t, c):
    fam.append((label, name, t, c))


cnt = lambda rs, f: (sum(1 for r in rs if f(r)), len(rs))
add("H1", "superpowers pass, BUG+CROSS", cnt(sel(arm="superpowers", q=hard), lambda r: r["passed"]), cnt(sel(arm="none", q=hard), lambda r: r["passed"]))
add("H2", "pocock pass, BUG+CROSS", cnt(sel(arm="pocock", q=hard), lambda r: r["passed"]), cnt(sel(arm="none", q=hard), lambda r: r["passed"]))
add("H7", "pstack pass, Cursor", cnt(sel(arm="pstack"), lambda r: r["passed"]), cnt(sel(arm="none", agent="cursor"), lambda r: r["passed"]))
for a in ["superpowers", "pocock", "pstack"]:
    add("H4", f"{a}: BUG test that bites (original)", cnt(sel(arm=a, q="BUG"), lambda r: bite.get(r["key"]) == "bites"),
        cnt(sel(arm="none", q="BUG"), lambda r: bite.get(r["key"]) == "bites"))
for a in ["superpowers", "pocock", "pstack"]:
    ags = sorted({r["agent"] for r in sel(arm=a)})
    add("H5", f"{a}: test-file-first", cnt(sel(arm=a), lambda r: r["test_first"] == "True"),
        cnt(sel(arm="none", agent=ags), lambda r: r["test_first"] == "True"))
ps = [fisher_greater(t[0], t[1], c[0], c[1]) for _, _, t, c in fam]
adj = holm(ps)
P("| # | comparison | pack | none | difference (95% CI) | p | Holm p |\n| --- | --- | --- | --- | --- | --- | --- |")
for (lab, name, t, c), p, h in zip(fam, ps, adj):
    P(f"| {lab} | {name} | {t[0]}/{t[1]} | {c[0]}/{c[1]} | {rd(t[0], t[1], c[0], c[1])} | {p:.3f} | {h:.3f} |")
P("\nReading the intervals: a pass-rate interval that includes 0 means no improvement was demonstrated. It is not evidence "
  "of no effect: the H1 interval also includes gains of the size shown by its upper bound.\n")

# 2. Task clustering and ceiling
P("## 2. Where the pass-rate evidence comes from (task clustering and ceiling)\n")
P("The 6 runs in a cell repeat one task. The independent units for generalising to other tasks are the 3 tasks "
  "(6 task-agent cells), not the runs. Pass rate per task-agent cell:\n")
P("| task | agent | " + " | ".join(ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
ceiling = 0
for q in TASKS:
    for g in AGENTS:
        cells = []
        for a in ARMS:
            rs = sel(q=q, agent=g, arm=a)
            cells.append(f"{sum(r['passed'] for r in rs)}/{len(rs)}" if rs else "-")
        n = sel(q=q, agent=g, arm="none")
        ceiling += all(r["passed"] for r in n)
        P(f"| {q} | {g} | " + " | ".join(cells) + " |")
P(f"\n`none` passed every run in {ceiling} of 6 task-agent cells. A pack can only show a gain where the control fails, "
  "which here is one cell: Codex on CROSS (4/6). Every pass-rate difference in favour of a pack comes from that cell.\n")
cx = lambda a: cnt(sel(arm=a, q="CROSS", agent="codex"), lambda r: r["passed"])
for a in ["superpowers", "placebo", "pocock"]:
    t, c = cx(a), cx("none")
    P(f"- Codex CROSS, {a} {t[0]}/{t[1]} vs none {c[0]}/{c[1]}: difference {rd(t[0], t[1], c[0], c[1])}, "
      f"one-sided p {fisher_greater(t[0], t[1], c[0], c[1]):.3f}.")
t = cnt(sel(arm="superpowers", agent="codex", q=hard), lambda r: r["passed"])
c = cnt(sel(arm="none", agent="codex", q=hard), lambda r: r["passed"])
P(f"- Exploratory, Codex only, BUG+CROSS: superpowers {t[0]}/{t[1]} vs none {c[0]}/{c[1]}, "
  f"difference {rd(t[0], t[1], c[0], c[1])}, one-sided p {fisher_greater(t[0], t[1], c[0], c[1]):.3f}.\n")

# 3. Pocock uptake
P("## 3. Pocock: did the skills run?\n")
P("| task | agent | runs that read a Pocock skill | passed when read | passed when not read |\n| --- | --- | --- | --- | --- |")
for q in TASKS:
    for g in AGENTS:
        rs = sel(arm="pocock", q=q, agent=g)
        rd_, nr = [r for r in rs if r["skill_read"]], [r for r in rs if not r["skill_read"]]
        P(f"| {q} | {g} | {len(rd_)}/{len(rs)} | {sum(r['passed'] for r in rd_)}/{len(rd_)} | {sum(r['passed'] for r in nr)}/{len(nr)} |")
P("\nExploratory and confounded with task: reading a skill is almost entirely determined by which task it is. The H2 "
  "result is a test of the pack as installed. On CROSS and FEAT it says little about Pocock's instructions, which mostly "
  "were never read.\n")

# 4. Mutation (retrospective H4)
P("## 4. Tests that bite, per defect (retrospective)\n")
ctrl = mut.get("control/hidden", {})
P(f"Control: the hidden test, run through the same harness, is classified `{ctrl.get('verdict')}` "
  "(it detects each defect on its own and passes on the fixed code).\n")
V = ["both", "price-only", "mapper-only", "combined-only", "none", "fails-on-fixed", "not-executable", "no-tests"]
P("| agent | arm | " + " | ".join(V) + " |\n| --- | --- |" + " --- |" * len(V))
for g in AGENTS:
    for a in ARMS:
        ks = [r["key"] for r in sel(q="BUG", agent=g, arm=a)]
        if not ks:
            continue
        c = Counter(mut.get(k, {}).get("verdict", "missing") for k in ks)
        P(f"| {g} | {a} | " + " | ".join(str(c.get(v, 0)) for v in V) + " |")
both = lambda a, ag=None: cnt(sel(arm=a, q="BUG", **({"agent": ag} if ag else {})), lambda r: mut.get(r["key"], {}).get("verdict") == "both")
P("")
for a in ["superpowers", "pocock", "pstack"]:
    ags = sorted({r["agent"] for r in sel(arm=a)})
    t = both(a)
    c = cnt(sel(arm="none", q="BUG", agent=ags), lambda r: mut.get(r["key"], {}).get("verdict") == "both")
    P(f"- Exploratory: {a} runs whose tests catch both defects independently, {t[0]}/{t[1]} vs none {c[0]}/{c[1]}: "
      f"difference {rd(t[0], t[1], c[0], c[1])}, one-sided p {fisher_greater(t[0], t[1], c[0], c[1]):.3f}.")
for g in AGENTS:
    for a in ["none", "superpowers"]:
        t = cnt(sel(arm=a, q="BUG", agent=g), lambda r: mut.get(r["key"], {}).get("verdict") == "both")
        P(f"- {g} {a}: {t[0]}/{t[1]} catch both defects.")
P("On Codex the control already caught both defects in every run, so the pooled gaps come from Cursor, where `none` "
  "rarely wrote a test at all.")
fails = [r for r in sel(q="BUG") if not r["passed"]]
P("\nThe four failed BUG runs: " + "; ".join(f"`{r['key']}` {mut.get(r['key'], {}).get('verdict')}" for r in fails) + ".\n")

# 5. TDD evidence
P("## 5. Test-file-first and evidence of TDD (retrospective)\n")
T = ["tdd-confirmed", "test-file-first", "impl-first", "no-test-edits", "unknown"]
P("| agent | arm | test-file-first (H5) | " + " | ".join(T) + " |\n| --- | --- | --- |" + " --- |" * len(T))
for g in AGENTS:
    for a in ARMS:
        rs = sel(agent=g, arm=a)
        if not rs:
            continue
        c = Counter(proc[r["key"]]["tdd"] for r in rs)
        P(f"| {g} | {a} | {sum(r['test_first'] == 'True' for r in rs)}/{len(rs)} | " + " | ".join(str(c.get(v, 0)) for v in T) + " |")
why = Counter((r["arm"], proc[r["key"]]["tdd"], proc[r["key"]]["tdd_reason"]) for r in rows
              if proc[r["key"]]["tdd"] in ("test-file-first", "unknown"))
P("\nWhy runs were not confirmed: " + "; ".join(f"{a} {v} ({w}) ×{n}" for (a, v, w), n in sorted(why.items())) + ".\n")
for a in ["superpowers", "pocock", "pstack"]:
    ags = sorted({r["agent"] for r in sel(arm=a)})
    tr, cr = sel(arm=a), sel(arm="none", agent=ags)
    known = [r for r in tr if proc[r["key"]]["tdd"] != "unknown"]
    t = cnt(tr, lambda r: proc[r["key"]]["tdd"] == "tdd-confirmed")
    c = cnt(cr, lambda r: proc[r["key"]]["tdd"] == "tdd-confirmed")
    P(f"- Exploratory: {a} confirmed TDD in {t[0]}/{t[1]} runs ({len(tr) - len(known)} unknown) vs none {c[0]}/{c[1]}: "
      f"difference {rd(t[0], t[1], c[0], c[1])}.")
P("")

# 6. Cost and effort, reconciled
P("## 6. Cost and effort (reconciled)\n")
P("Two relative-cost figures were published and they use different methods. `report.md` (the rig) divides each run's "
  "tokens by the `none` **mean** for the same task and agent, then averages. `analysis.md` takes the **median** of each "
  "run's tokens divided by the `none` median. Both are shown. Token totals include cached input; Codex counts cached input "
  "inside input, Cursor separately.\n")
P("| agent | arm | runs | mean total tokens | mean fresh input | mean cached input | mean output | relative (mean method) | relative (median method) | est. $ total | passes | est. $ per verified pass | median s | median Maven test runs | median production lines | median test lines |")
P("|" + " --- |" * 16)


def fresh_cached(g, t):
    return (t["input"] - t["cache_read"], t["cache_read"]) if g == "codex" else (t["input"] + t["cache_write"], t["cache_read"])


for g in AGENTS:
    bm = {q: st.mean(r["tok"]["total"] for r in sel(agent=g, arm="none", q=q)) for q in TASKS}
    bmed = {q: st.median(r["tok"]["total"] for r in sel(agent=g, arm="none", q=q)) for q in TASKS}
    for a in ARMS:
        rs = sel(agent=g, arm=a)
        if not rs:
            continue
        fc = [fresh_cached(g, r["tok"]) for r in rs]
        cost = sum(float(r["cost"]) for r in rs)
        npass = sum(r["passed"] for r in rs)
        rel_mean = st.mean(r["tok"]["total"] / bm[r["q"]] for r in rs)
        rel_med = st.median(r["tok"]["total"] / bmed[r["q"]] for r in rs)
        prod = [int(r["diff_lines"]) for r in rs]
        ns = {r["key"]: r for r in rs}
        tl, ml = [], []
        for k in ns:
            lines = [l.split("\t") for l in open(os.path.join(R, "stage1/runs", k, "agent.numstat")).read().splitlines() if l]
            tl.append(sum(int(x) + int(y) for x, y, p in lines if x != "-" and "/src/test/" in p))
            ml.append(sum(int(x) + int(y) for x, y, p in lines if x != "-" and "/src/test/" not in p))
        P(f"| {g} | {a} | {len(rs)} | {st.mean(r['tok']['total'] for r in rs) / 1e6:.2f}M | {st.mean(f for f, _ in fc) / 1e6:.2f}M | "
          f"{st.mean(c for _, c in fc) / 1e6:.2f}M | {st.mean(r['tok']['output'] for r in rs) / 1e3:.0f}k | {rel_mean:.2f} | {rel_med:.2f} | "
          f"{cost:.2f} | {npass} | {cost / npass:.3f} | {st.median(float(r['seconds']) for r in rs):.0f} | "
          f"{st.median(proc[r['key']]['test_runs'] for r in rs):.0f} | {st.median(ml):.0f} | {st.median(tl):.0f} |")
P("\nDollar figures are estimates at list prices: Codex $0.20, $0.02 and $1.20 per million fresh-input, cached-input and "
  "output tokens; Cursor $2 per million for all input including cache reads (the design's rule, an upper bound) and $6 "
  "per million output. Nothing here is a billed amount. Cost per verified pass is total estimated spend divided by "
  "passing runs. With most cells at the ceiling it mostly restates relative cost, and it is not a measure of value.\n")
P("Attribution: the logs show that pack runs make more turns and more Maven test runs and add test code, while the "
  "production change stays the same size. They do not show what share of the extra tokens each of those causes, because "
  "most tokens are context re-sent on every turn.\n")

# 7. Audits
reg = audit["regrade"]
P("## 7. Grading and isolation audits\n")
P(f"- Independent regrade from the Maven logs: agrees with the recorded grade on {sum(v['agree'] for v in reg.values())}/{len(reg)} runs.")
P(f"- Hidden suites ran their full count with nothing skipped in {sum(1 for k, v in reg.items() if v['hidden_run'] == audit['expected_hidden'][k.split('/')[0]] and not v['hidden_skipped'])}/{len(reg)} runs.")
P(f"- `none` and `placebo` runs with any trace of a pack skill in their event logs: {sum(1 for v in audit['isolation'].values() if v)}/{len(audit['isolation'])}.")
print("\n".join(out))
