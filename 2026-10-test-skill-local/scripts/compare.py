"""Local against hosted, fixed before the measured runs (README, "Hypotheses and analysis").

Hosted: 2026-10-test-skill's published runs (results/stage1, -medium, -gate), cited at e3908706; checked unchanged in git.
Local: this folder's results/stage1, -medium, -gate (arms A to F), and results/stage1-stop (arm G, exploratory only).
Loading, the sign-flip test and the bootstrap are analyse.py's own code (its definitions are executed, not copied), and
Holm is 2026-10-skills-impact/scripts/stats.py's.

Primary: for each arm A to F, verified passes per task, local minus hosted (0 to 3 each); two-sided exact sign-flip over
tasks, bootstrap 95% CI (10,000 resamples, seed 1), Holm across the six arms. Secondary (two-sided, unadjusted): relevant
tests local vs hosted per arm; each TSK arm effect for both models side by side, and their per-task difference; tokens,
time, cost, energy, false success claims, failure modes. Exploratory: arm G vs arm A (local). Calibration: hosted runs
made on this machine (results/calibration), against TSK's arm A.
Usage: python3 -I compare.py [local results dir] [local stages, comma-separated] > results/compare.md
"""
import ast, csv, glob, gzip, json, os, re, statistics as st, subprocess, sys
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE)
O = os.path.join(N, "..", "2026-10-test-skill")
SHA = "e3908706a9278546408fdd462a0ae685ef98255b"
STAGES = ["stage1", "stage1-medium", "stage1-gate"]
KWH_GBP = 0.25

src = open(os.path.join(HERE, "analyse.py")).read()
ns = {"__file__": os.path.join(HERE, "analyse.py"), "__name__": "analyse_defs"}
ARGV = sys.argv[:]; sys.argv = [sys.argv[0]]
tree = ast.parse(src)  # imports, top-level constants before the analysis, and every function: none of the printing code
first_rows = next(i for i, n in enumerate(tree.body) if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "rows")
tree.body = [n for i, n in enumerate(tree.body) if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
             or (i < first_rows and isinstance(n, (ast.Assign, ast.Expr)))]
exec(compile(tree, "analyse.py", "exec"), ns)
load, signflip_p, boot, cost, holm, LABEL = ns["load"], ns["signflip_p"], ns["boot"], ns["cost"], ns["holm"], ns["LABEL"]
ARMS = ["none", "instruction", "skill", "skill-revised", "medium", "gate"]


def usage(rd):
    """Token usage with reasoning: the last turn.completed in the events, else the session file (timed-out runs)."""
    raw = os.path.join(rd, "raw.out")
    text = (open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")).read()
    u = None
    for line in text.splitlines():
        if '"turn.completed"' in line:
            u = json.loads(line).get("usage")
    if u is None and os.path.exists(os.path.join(rd, "session.json")):
        u = json.load(open(os.path.join(rd, "session.json"))).get("tokens")
    u = u or {}
    return {k: u.get(k, 0) or 0 for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")}


FAIL_RULES = ["timeout", "tool-call errors", "malformed edits", "gave up", "context overflow", "looping", "wrong fix"]
GAVE_UP = re.compile(r"\b(could not|couldn't|unable to|was not able to|cannot complete|can't complete)\b", re.I)


def failure_modes(rd, rec):
    raw = os.path.join(rd, "raw.out")
    text = (open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")).read()
    err = open(os.path.join(rd, "raw.err")).read() if os.path.exists(os.path.join(rd, "raw.err")) else ""
    cmds, outs = [], []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        it = e.get("item") or {}
        if e.get("type") == "item.completed" and it.get("type") == "command_execution":
            cmds.append(it.get("command", "")); outs.append(it.get("aggregated_output", ""))
    m = set()
    if rec.get("timed_out") or rec.get("status") == "timeout":
        m.add("timeout")
    if re.search(r"ERROR codex_core::tools|exec_command failed|tool call failed", err):
        m.add("tool-call errors")
    if any("Invalid patch" in o or "apply_patch verification failed" in o for o in outs):
        m.add("malformed edits")
    if GAVE_UP.search(rec.get("answer") or ""):
        m.add("gave up")
    if re.search(r"context.{0,40}(exceed|too long|length)|context_compacted|compact", err + text, re.I):
        m.add("context overflow")
    if cmds and Counter(cmds).most_common(1)[0][1] >= 5:
        m.add("looping")
    if not m:
        m.add("wrong fix")
    return m


def enrich(base, stages):
    """load() per stage, plus each run's usage, failure modes, start time and stage. load() walks the same sorted glob,
    so its rows line up one to one with the run folders."""
    out = []
    for s in stages:
        rd0 = os.path.join(base, s, "runs")
        if not os.path.isdir(rd0):
            continue
        files = sorted(glob.glob(os.path.join(rd0, "*/*/codex/*/run.json")))
        for f, r in zip(files, load(rd0)):
            d = json.load(open(f)); rd = os.path.dirname(f)
            assert (r["task"], r["arm"]) == (d["question"], d["arm"])
            out.append(dict(r, rep=d["rep"], usage=usage(rd), modes=failure_modes(rd, d) if not r["passed"] else set(),
                            started=datetime.fromisoformat(d["started"]).timestamp(), stage=s))
    return out


def energy_wh(base, stage, r):
    p = os.path.join(base, stage, "power.csv")
    if not os.path.exists(p):
        return None
    rows = [(float(t), float(w)) for t, w in list(csv.reader(open(p)))[1:]]
    seg = [x for x in rows if r["started"] <= x[0] <= r["started"] + r["seconds"]]
    return sum((b[0] - a[0]) * a[1] for a, b in zip(seg, seg[1:])) / 3600 if len(seg) > 1 else None


hosted_dirty = subprocess.run(["git", "-C", O, "diff", "--quiet", SHA, "--", "results"], capture_output=True).returncode
LR = ARGV[1] if len(ARGV) > 1 else os.path.join(N, "results")  # optional: another results folder (for testing)
LSTAGES = ARGV[2].split(",") if len(ARGV) > 2 else STAGES + ["stage1-stop"]  # optional: local stages, e.g. "pilot"
H_ALL = enrich(os.path.join(O, "results"), STAGES)
LOC = enrich(LR, LSTAGES)
L = [r for r in LOC if r["arm"] != "stop"]
G = [r for r in LOC if r["arm"] == "stop"]
tasks = sorted({r["task"] for r in LOC}) or sorted({r["task"] for r in H_ALL})  # the pilot uses 10 of the 20 tasks
H = [r for r in H_ALL if r["task"] in tasks]
U = 6  # per-task rates in units of 1/6, so 1, 2 or 3 runs per cell give whole numbers (exact sign-flip, no float ties)


def cnt(rows, t, a, key):
    return sum(r[key] for r in rows if r["task"] == t and r["arm"] == a)


def units(rows, t, a, key):
    """A cell's rate (passes over runs) in units of 1/U. With 3 runs on both sides this is 2 x the count difference,
    which leaves the sign-flip p and the bootstrap interval of the rate exactly as in the design."""
    rs = [r[key] for r in rows if r["task"] == t and r["arm"] == a]
    return round(U * sum(rs) / len(rs)) if rs else 0


def total(rows, a, key):
    rs = [r for r in rows if r["arm"] == a]
    return f"{sum(r[key] for r in rs)}/{len(rs)}"


def diff_stats(d, two_sided=True):
    rate = [x / U for x in d]
    return st.mean(rate), boot(rate), signflip_p(d, two_sided)


def bsw(d):
    return f"{sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)}"


def pts(m, lo, hi):
    return f"{m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f})"


print("# test-skill-local: local against hosted\n")
print(f"Hosted: 2026-10-test-skill results at `{SHA[:8]}` ({'UNCHANGED' if hosted_dirty == 0 else 'CHANGED SINCE'} in git), "
      f"{len(H)} runs. Local: {len(L)} runs (A to F), {len(G)} runs (G). Local statuses: {dict(Counter(r['status'] for r in L + G))}; "
      f"fully graded: {sum(r['graded'] for r in L + G)}/{len(L + G)}.\n")
arms = [a for a in ARMS if any(r["arm"] == a for r in L)]

print("## Verified passes, local against hosted (primary)\n")
print("| # | arm | hosted | local | tasks local better / same / worse | mean per-task difference (95% CI) | p (two-sided) | Holm p |")
print("| --- | --- | --- | --- | --- | --- | --- | --- |")
res = {a: [units(L, t, a, "passed") - units(H, t, a, "passed") for t in tasks] for a in arms}
ps = {a: diff_stats(res[a])[2] for a in arms}
adj = dict(zip(arms, holm([ps[a] for a in arms]))) if arms else {}
for a in arms:
    m, (lo, hi), p = diff_stats(res[a])
    print(f"| L-{'ABCDEF'[ARMS.index(a)]} | {LABEL[a]} | {total(H, a, 'passed')} | {total(L, a, 'passed')} | {bsw(res[a])} | {pts(m, lo, hi)} | {p:.3f} | {adj[a]:.3f} |")

print("\n## Per task (verified passes, hosted / local; each of the runs made)\n")
print("| task | " + " | ".join(LABEL[a] for a in arms) + " |\n| --- |" + " --- |" * len(arms))
for t in tasks:
    print(f"| {t} | " + " | ".join(f"{cnt(H, t, a, 'passed')} / {cnt(L, t, a, 'passed')}" for a in arms) + " |")

print("\n## Relevant tests, local against hosted (secondary, two-sided, unadjusted)\n")
print("| arm | hosted | local | tasks local better / same / worse | difference (95% CI) | p |\n| --- | --- | --- | --- | --- | --- |")
for a in arms:
    d = [units(L, t, a, "relevant") - units(H, t, a, "relevant") for t in tasks]
    m, (lo, hi), p = diff_stats(d)
    print(f"| {LABEL[a]} | {total(H, a, 'relevant')} | {total(L, a, 'relevant')} | "
          f"{bsw(d)} | {pts(m, lo, hi)} | {p:.3f} |")

print("\n## TSK's arm effects, both models side by side (secondary, two-sided, unadjusted)\n")
print("| measure | effect | hosted (95% CI), p | local (95% CI), p | local effect minus hosted effect (95% CI), p |")
print("| --- | --- | --- | --- | --- |")
EFFECTS = [("relevant", "instruction", "none"), ("relevant", "skill", "instruction"), ("relevant", "skill-revised", "skill"),
           ("relevant", "gate", "instruction")] + [("passed", a, "none") for a in ARMS[1:]] + \
          [("passed", "gate", "instruction"), ("passed", "medium", "gate")]
for key, a, b in EFFECTS:
    if a not in arms or b not in arms:
        continue
    dh = [units(H, t, a, key) - units(H, t, b, key) for t in tasks]
    dl = [units(L, t, a, key) - units(L, t, b, key) for t in tasks]
    dd = [x - y for x, y in zip(dl, dh)]
    cells = []
    for d in (dh, dl, dd):
        m, (lo, hi), p = diff_stats(d)
        cells.append(f"{pts(m, lo, hi)}, p {p:.3f}")
    print(f"| {key} | {a} vs {b} | " + " | ".join(cells) + " |")


def cost_rows(rows, local):
    out = []
    for a in sorted({r["arm"] for r in rows}, key=lambda x: (ARMS + ["stop"]).index(x)):
        rs = [r for r in rows if r["arm"] == a]
        u = lambda k: st.mean(r["usage"][k] for r in rs) / 1e6  # noqa: E731
        usd = sum(r["cost"] for r in rs); npass = sum(r["passed"] for r in rs)
        e = [energy_wh(LR, r["stage"], r) for r in rs] if local else []
        e = [x for x in e if x is not None]
        failed = [r for r in rs if not r["passed"]]
        out.append(f"| {'local' if local else 'hosted'} | {LABEL[a]} | {len(rs)} | {npass} | {u('input_tokens'):.2f}M | "
                   f"{u('cached_input_tokens'):.2f}M | {u('output_tokens'):.3f}M | {u('reasoning_output_tokens'):.3f}M | "
                   f"{st.median(r['seconds'] for r in rs):.0f} | {sum(r['seconds'] for r in rs) / 3600:.1f} | "
                   f"{usd:.2f}{' (equivalent)' if local else ''} | {(usd / npass if npass else float('inf')):.3f} | "
                   + (f"{sum(e) / 1000:.2f} kWh, £{sum(e) / 1000 * KWH_GBP:.2f} ({len(e)}/{len(rs)} runs logged)" if e else "-")
                   + f" | {sum(r['overclaim'] for r in failed)}/{len(failed)} |")
    return out


print("\n## Tokens, time, cost and claims (secondary)\n")
print("Hosted $ at TSK's list prices; local $ is what the same tokens would cost at those prices. Energy: APU package "
      f"power (CPU and GPU), integrated over each run's agent time, at £{KWH_GBP}/kWh.\n")
print("| model | arm | runs | passed | mean input | mean cached | mean output | mean reasoning | median s | total h | $ | "
      "$ per pass | energy | false success claims (of failed) |")
print("| --- |" + " --- |" * 13)
for line in cost_rows(H, False) + cost_rows(L, True):
    print(line)

print("\n## Failure modes of failed runs (secondary; a run can have several)\n")
print("| model | arm | failed | " + " | ".join(FAIL_RULES) + " |\n| --- | --- | --- |" + " --- |" * len(FAIL_RULES))
for name, rows in (("hosted", H), ("local", L), ("local", G)):
    for a in sorted({r["arm"] for r in rows}, key=lambda x: (ARMS + ["stop"]).index(x)):
        f = [r for r in rows if r["arm"] == a and not r["passed"]]
        c = Counter(m for r in f for m in r["modes"])
        print(f"| {name} | {LABEL[a]} | {len(f)} | " + " | ".join(str(c[k]) for k in FAIL_RULES) + " |")

if G and any(r["arm"] == "none" for r in L):
    print("\n## Exploratory: arm G (stop) against arm A (none), local only\n")
    d = [units(G, t, "stop", "passed") - units(L, t, "none", "passed") for t in tasks]
    m, (lo, hi), p = diff_stats(d)
    A = [r for r in L if r["arm"] == "none"]
    print(f"- Verified passes: G {sum(r['passed'] for r in G)}/{len(G)}, A {sum(r['passed'] for r in A)}/{len(A)}; per task {bsw(d)}; "
          f"{pts(m, lo, hi)}, p {p:.3f} (two-sided, unadjusted, exploratory).")
    print(f"- Timeouts: G {sum(r['status'] == 'timeout' for r in G)}, A {sum(r['status'] == 'timeout' for r in A)}. "
          f"Median seconds: G {st.median(r['seconds'] for r in G):.0f}, A {st.median(r['seconds'] for r in A):.0f}. "
          f"Mean tokens: G {st.mean(r['tokens'] for r in G) / 1e6:.2f}M, A {st.mean(r['tokens'] for r in A) / 1e6:.2f}M.")

C = enrich(LR, ["calibration"])
if C:
    print("\n## Calibration: hosted model on this machine against TSK's arm A (descriptive)\n")
    print("| task | TSK arm A (of 3) | this machine (of 1) |\n| --- | --- | --- |")
    ct = sorted({r["task"] for r in C})
    for t in ct:
        print(f"| {t} | {cnt(H_ALL, t, 'none', 'passed')} | {cnt(C, t, 'none', 'passed')} |")
    agree = sum((cnt(C, t, 'none', 'passed') == 1) == (cnt(H_ALL, t, 'none', 'passed') >= 2) for t in ct)
    print(f"\nPassed here: {sum(r['passed'] for r in C)}/{len(C)}; TSK arm A: {sum(cnt(H_ALL, t, 'none', 'passed') for t in ct)}/{3 * len(ct)}. "
          f"Tasks where this run agrees with TSK's majority: {agree}/{len(ct)}.")
