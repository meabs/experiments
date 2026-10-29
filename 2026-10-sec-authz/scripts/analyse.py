"""Analysis for sec-authz, fixed before the measured runs (README, "Hypotheses and analysis").

Primary: secure functional completion. A run passes if it finished (status ok) and grade.json says pass: it builds,
and every functional_, allows_ and denies_ hidden test and every existing test passes. Arms are compared by the mean
over the eight tasks of each task's pass rate, so every task counts equally.

- H2 B > A, H3 C > B (and C > A): one-sided permutation tests, arm labels shuffled within each task, 100,000 shuffles,
  seed 1; Holm over these three at alpha 0.05. Effect intervals: bootstrap within tasks, 10,000 resamples, seed 1.
- H1 (baseline agents sometimes ship working but insecure endpoints) and H4 (D adds little over C) are estimates, not
  tests: H1 is the rate of insecure functional completion in arm A with a Wilson 95% interval; H4 is D minus C with its
  bootstrap interval (and D minus B).
- Secondary: functional pass, security pass, insecure functional completion (split into access breaches and wrong
  denial code only), legitimate access blocked, regressions, breach categories, skill read / gate run, false success claims, tokens, cost, wall time.

Usage: python3 -I analyse.py <out dir> > results/analysis.md   (out dir holds <arm>/runs/<task>/<arm>/codex/<rep>/)
"""
import glob, gzip, json, os, random, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-skills-impact", "scripts"))
from stats import holm, wilson  # noqa: E402

ARMS = ["A", "B", "C", "D"]
NAMES = {"A": "baseline", "B": "security skill", "C": "security gate", "D": "skill + gate"}
TASKS = [f"S0{i}" for i in range(1, 9)]
PERMS, BOOTS, SEED = 100_000, 10_000, 1
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}  # gpt-5.6-luna list prices, $ per million tokens
# Failure category of each denies_ test, from words in its name (first match wins).
CATEGORIES = [
    ("scope", ["Scope", "scope"]),
    ("tenant", ["Tenant", "tenant"]),
    ("assignment", ["unassigned", "Unassigned", "AssignedToTheAccount", "UnassignedCustomers"]),
    ("workflow (four-eyes)", ["selfApproval"]),
    ("field-level permission", ["Limit"]),
    ("data exposure", ["Internal", "RiskScore", "OnlyThisCustomers", "IdNameAndEmail"]),
    ("role", ["Role", "role", "support", "Support", "customers", "Customers", "admin", "Admin"]),
    ("ownership", ["otherCustomer", "others", "Others"]),
    ("missing or anonymous", ["missing", "unknown", "unauthenticated", "Missing", "Unknown"]),
]


def category(test):
    name = test.split(".")[-1].split(":")[0]
    for cat, words in CATEGORIES:
        if any(w in name for w in words):
            return cat
    return "other"


def read(path):
    if os.path.exists(path):
        return open(path, errors="replace").read()
    if os.path.exists(path + ".gz"):
        return gzip.open(path + ".gz", "rt", errors="replace").read()
    return ""


def load(out):
    runs = []
    for f in glob.glob(os.path.join(out, "*", "runs", "*", "*", "codex", "*", "run.json")):
        r = json.load(open(f))
        if r["arm"] not in ARMS or r["question"] not in TASKS:
            continue
        d = os.path.dirname(f)
        g = json.loads(read(os.path.join(d, "grade.json")) or "{}")
        if "denies_breach" not in g:  # graded before the severity split: derive it from the failure messages
            swap = ("expected:<404> but was:<403>", "expected:<403> but was:<404>")
            failed = [f for f in g.get("failed", []) if ".denies_" in f]
            g["denies_breach"] = [f.split(":")[0].split(".")[-1] for f in failed if not any(x in f for x in swap)]
        ok = r["status"] == "ok"
        full = lambda k: g.get(k, {}).get("total", 0) > 0 and g[k]["passed"] == g[k]["total"]
        functional = ok and g.get("build", False) and full("functional")
        allows, denies = full("allows"), full("denies")
        calls = " ".join(c.get("text", "") for c in r.get("tool_calls") or [])
        tok = r.get("tokens") or {}
        cached = tok.get("cache_read") or 0
        runs.append({
            "task": r["question"], "arm": r["arm"], "rep": r["rep"], "status": r["status"],
            "pass": 1 if ok and g.get("pass") else 0,
            "functional": functional, "security": ok and g.get("build", False) and allows and denies,
            "insecure_functional": functional and allows and not denies,
            "blocked": ok and g.get("build", False) and not allows,
            "regression": ok and g.get("build", False) and g.get("regression", {}).get("passed", 0) < 25,
            "build": g.get("build", False),
            "breach": functional and allows and bool(g.get("denies_breach")),
            "code_only": functional and allows and not denies and not g.get("denies_breach"),
            "categories": sorted({category(t) for t in g.get("denies_breach", [])}),
            "read_skill": "spring-api-authorisation/SKILL.md" in calls,
            "ran_gate": "verify-authz" in calls,
            "protected": [p for p in read(os.path.join(d, "protected.txt")).split() if p],
            "claim": r.get("claim_match"),
            "seconds": r["seconds"], "tokens": tok.get("total"),
            "cost": ((tok.get("input", 0) - cached) * PRICE["input"] + cached * PRICE["cached"]
                     + tok.get("output", 0) * PRICE["output"]) / 1e6,
            "left": "code/experiments" in read(os.path.join(d, "raw.out")),
        })
    return runs


def by_task(runs, arm, key="pass"):
    return {t: [int(r[key]) for r in runs if r["arm"] == arm and r["task"] == t] for t in TASKS}


def stat(a, b):
    ts = [t for t in TASKS if a[t] and b[t]]
    return st.mean(st.mean(a[t]) - st.mean(b[t]) for t in ts) if ts else float("nan")


def perm_greater(a, b, rng):
    obs = stat(a, b)
    hits = 0
    for _ in range(PERMS):
        pa, pb = {}, {}
        for t in TASKS:
            pool = a[t] + b[t]
            rng.shuffle(pool)
            pa[t], pb[t] = pool[: len(a[t])], pool[len(a[t]):]
        if stat(pa, pb) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (PERMS + 1)


def boot(a, b, rng):
    vals = []
    for _ in range(BOOTS):
        ra = {t: [rng.choice(a[t]) for _ in a[t]] if a[t] else [] for t in TASKS}
        rb = {t: [rng.choice(b[t]) for _ in b[t]] if b[t] else [] for t in TASKS}
        vals.append(stat(ra, rb))
    vals = sorted(v for v in vals if v == v)
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]) if vals else (float("nan"), float("nan"))


def pts(x):
    return "n/a" if x != x else f"{x * 100:+.1f} points"


def pct(n, d):
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "0/0"


def main(out):
    runs = load(out)
    rng = random.Random(SEED)
    arms = [a for a in ARMS if any(r["arm"] == a for r in runs)]
    print("# sec-authz: analysis\n")
    print(f"{len(runs)} runs from `{out}`. A pass (secure functional completion) means the run finished, the code built, "
          "and every functional, permitted-access, denied-access and existing test passed.\n")

    print("## Secure functional completion by arm and task (runs passed, higher is better)\n")
    print("| Task | " + " | ".join(f"{a} ({NAMES[a]})" for a in arms) + " |")
    print("| --- |" + " --- |" * len(arms))
    for t in TASKS:
        print(f"| {t} | " + " | ".join(
            (lambda v: f"{sum(v)}/{len(v)}" if v else "-")(by_task(runs, a)[t]) for a in arms) + " |")
    print("| **Total** | " + " | ".join(
        f"**{pct(sum(r['pass'] for r in runs if r['arm'] == a), sum(r['arm'] == a for r in runs))}**" for a in arms) + " |\n")

    print("## Hypotheses\n")
    rs = [r for r in runs if r["arm"] == "A"]
    n = sum(r["insecure_functional"] for r in rs)
    lo, hi = wilson(n, len(rs)) if rs else (0, 0)
    nb = sum(r["breach"] for r in rs)
    blo, bhi = wilson(nb, len(rs)) if rs else (0, 0)
    print(f"- **H1** (estimate): in arm A, {pct(n, len(rs))} of runs were insecure functional completions (working, "
          f"but failing a denied-access test); Wilson 95% interval {lo * 100:.0f}% to {hi * 100:.0f}%. Of these, "
          f"{pct(nb, len(rs))} were access breaches (allowed, leaked data or changed state; interval {blo * 100:.0f}% to "
          f"{bhi * 100:.0f}%), the rest only refused with the wrong code (403 where the API's convention is 404, or the "
          f"reverse).\n")
    print("Tested (one-sided, Holm-adjusted together). Effect: mean over tasks of the difference in pass rate, in "
          "percentage points; positive favours the first arm.\n")
    tests = [("H2", "B (skill) passes more than A (baseline)", "B", "A"),
             ("H3", "C (gate) passes more than B (skill)", "C", "B"),
             ("C vs A", "C (gate) passes more than A (baseline)", "C", "A")]
    res = []
    for hid, text, x, y in tests:
        a, b = by_task(runs, x), by_task(runs, y)
        if not any(a.values()) or not any(b.values()):
            continue
        res.append((hid, text, stat(a, b), *boot(a, b, rng), perm_greater(a, b, rng)))
    if res:
        print("| # | Hypothesis | Effect (95% interval) | p | Holm p | Verdict |")
        print("| --- | --- | --- | --- | --- | --- |")
        for (hid, text, eff, lo, hi, p), q in zip(res, holm([r[-1] for r in res])):
            print(f"| {hid} | {text} | {pts(eff)} ({pts(lo)} to {pts(hi)}) | {p:.4f} | {q:.4f} | "
                  f"{'confirmed' if q < 0.05 else 'no measurable difference'} |")
    for hid, x, y in [("H4", "D", "C"), ("D vs B", "D", "B")]:
        a, b = by_task(runs, x), by_task(runs, y)
        if any(a.values()) and any(b.values()):
            lo, hi = boot(a, b, rng)
            print(f"\n- **{hid}** (estimate): {x} minus {y}, {pts(stat(a, b))} (95% interval {pts(lo)} to {pts(hi)}).")
    print()

    print("## Did the arms happen as designed?\n")
    for a, key, what in [("B", "read_skill", "read the skill"), ("D", "read_skill", "read the skill"),
                         ("C", "ran_gate", "ran the gate"), ("D", "ran_gate", "ran the gate")]:
        rs = [r for r in runs if r["arm"] == a]
        if rs:
            k = sum(r[key] for r in rs)
            print(f"- `{a}`: {k} of {len(rs)} runs {what}"
                  f"{'' if k >= 0.75 * len(rs) else ' (fewer than three quarters: the arm did not happen as designed)'}.")
    left = [f"{r['task']} {r['arm']} {r['rep']}" for r in runs if r["left"]]
    print(f"- Runs that named the experiments folder (hidden tests): {len(left)}{' (' + ', '.join(left) + ')' if left else ''}.")
    prot = [f"{r['task']} {r['arm']} {r['rep']}" for r in runs if r["protected"]]
    print(f"- Runs that edited test support, existing tests or pom.xml (the grader used its own copies): {len(prot)}"
          f"{' (' + ', '.join(prot) + ')' if prot else ''}.\n")

    print("## Secondary (not tested)\n")
    print("| Arm | Runs | Secure functional completion (higher is better) | Functional pass (higher is better) | "
          "Security pass (higher is better) | Insecure functional completion (lower is better) | Legitimate access blocked "
          "(lower is better) | Regressions (lower is better) | Did not build (lower is better) | False success claims "
          "(lower is better) | Access breaches (lower is better) | Wrong denial code only (lower is better) |")
    print("| --- |" + " --- |" * 11)
    for a in arms:
        rs = [r for r in runs if r["arm"] == a]
        N = len(rs)
        print(f"| {a} | {N} | {pct(sum(r['pass'] for r in rs), N)} | {pct(sum(r['functional'] for r in rs), N)} | "
              f"{pct(sum(r['security'] for r in rs), N)} | {pct(sum(r['insecure_functional'] for r in rs), N)} | "
              f"{pct(sum(r['blocked'] for r in rs), N)} | {pct(sum(r['regression'] for r in rs), N)} | "
              f"{pct(sum(not r['build'] for r in rs), N)} | {sum(r['claim'] == 'false_pass' for r in rs)} of "
              f"{sum(not r['pass'] for r in rs)} failed runs | {pct(sum(r['breach'] for r in rs), N)} | "
              f"{pct(sum(r['code_only'] for r in rs), N)} |")
    print("\nA false success claim: the agent's closing verification line said its checks passed, but the hidden tests failed.\n")

    print("| Arm | Median wall time (lower is better) | Median tokens (lower is better) | Mean cost per run, $ list price "
          "(lower is better) | Total cost, $ | Timeouts |")
    print("| --- | --- | --- | --- | --- | --- |")
    for a in arms:
        rs = [r for r in runs if r["arm"] == a]
        tok = [r["tokens"] for r in rs if r["tokens"]]
        print(f"| {a} | {st.median(r['seconds'] for r in rs):.0f} s | {st.median(tok) / 1000 if tok else 0:.0f}k | "
              f"{st.mean(r['cost'] for r in rs):.3f} | {sum(r['cost'] for r in rs):.2f} | "
              f"{sum(r['status'] == 'timeout' for r in rs)} |")

    print("\n## Breach categories (runs with at least one access breach of that kind; wrong-code-only failures excluded)\n")
    cats = sorted({c for r in runs for c in r["categories"]})
    if cats:
        print("| Category | " + " | ".join(arms) + " |")
        print("| --- |" + " --- |" * len(arms))
        for c in cats:
            print(f"| {c} | " + " | ".join(str(sum(c in r["categories"] for r in runs if r["arm"] == a)) for a in arms) + " |")
    else:
        print("None.")


if __name__ == "__main__":
    main(sys.argv[1])
