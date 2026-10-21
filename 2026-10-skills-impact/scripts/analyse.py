"""Computes per-run measures and the pre-registered hypothesis tests for the skills-impact experiment.

Usage: python3 -I analyse.py <runs dir> [bite.json]. Writes runs.csv next to this script's results folder and prints
markdown tables. bite.json (optional) comes from bite.sh and holds the tests-that-bite result per BUG run.
"""
import csv, glob, gzip, json, math, os, re, statistics, sys

RUNS = sys.argv[1]
BITE = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else {}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
SKILL = re.compile(r"skills/.+/SKILL\.md")
ARMS = ["none", "placebo", "superpowers", "pocock", "pstack"]


def cost(agent, t):
    if agent == "codex":  # input includes cached input
        return ((t["input"] - t["cache_read"]) * 0.20 + t["cache_read"] * 0.02 + t["output"] * 1.20) / 1e6
    return ((t["input"] + t["cache_read"] + t["cache_write"]) * 2.0 + t["output"] * 6.0) / 1e6


def edit_order(agent, d, rdir):
    """Paths the agent edited, in order. Codex edits come from file_change events; Cursor from edit tool calls."""
    paths = []
    if agent == "codex":
        raw = os.path.join(rdir, "raw.out")
        for line in (open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            it = e.get("item") or {}
            if e.get("type") == "item.completed" and it.get("type") == "file_change":
                paths += [c["path"] for c in it.get("changes", [])]
    else:
        paths = [t["text"] for t in d.get("tool_calls") or [] if t["tool"] == "edit"]
    return paths


def test_first(paths):
    ti = next((i for i, p in enumerate(paths) if "/src/test/" in p), None)
    mi = next((i for i, p in enumerate(paths) if "/src/main/" in p), None)
    if ti is None or mi is None:
        return None
    return ti < mi


rows = []
for f in sorted(glob.glob(os.path.join(RUNS, "*/*/*/*/run.json"))):
    rdir = os.path.dirname(f)
    q, arm, agent, rep = rdir.split(os.sep)[-4:]
    d = json.load(open(f))
    s = json.load(open(os.path.join(rdir, "verify-summary.json")))
    claim = d.get("claim") or {}
    if isinstance(claim, str):
        claim = {}
    numstat = [l.split("\t") for l in open(os.path.join(rdir, "agent.numstat")).read().splitlines() if l.strip()]
    lines = sum(int(a) + int(b) for a, b, _ in numstat if a != "-")
    test_files = [p for _, _, p in numstat if "/src/test/" in p]
    tf = test_first(edit_order(agent, d, rdir))
    t = d["tokens"]
    rows.append(dict(
        q=q, arm=arm, agent=agent, rep=int(rep), status=d["status"], seconds=d["seconds"], turns=d["turns"],
        passed=bool(s["pass"]), hidden_pass=bool(s["hidden_pass"]), other_failures=s["other_failures"],
        tokens=t["total"], cost=round(cost(agent, t), 4),
        skill_read=any(SKILL.search(x.get("text", "")) for x in d.get("tool_calls") or []),
        claimed=claim.get("result", "none"), overclaim=claim.get("result") == "passed" and not s["pass"],
        diff_lines=lines, files=len(numstat), added_tests=bool(test_files), test_first=tf,
        bite=BITE.get(f"{q}/{arm}/{agent}/{rep}", ""),
    ))

with open(os.path.join(OUT, "runs.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def fisher_greater(a, n1, c, n2):
    """One-sided Fisher exact p that group 1 (a of n1) has a higher rate than group 2 (c of n2)."""
    k, N = a + c, n1 + n2
    comb = math.comb
    tot = comb(N, k)
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot


def sel(**kw):
    return [r for r in rows if all((r[k] in v) if isinstance(v, (list, tuple, set)) else r[k] == v for k, v in kw.items())]


def frac(rs, key):
    return f"{sum(1 for r in rs if r[key])}/{len(rs)}"


print("## Pass rate by cell\n")
print("| task | agent | " + " | ".join(ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
for q in ["BUG", "CROSS", "FEAT"]:
    for g in ["codex", "cursor"]:
        cells = [frac(sel(q=q, agent=g, arm=a), "passed") if sel(q=q, agent=g, arm=a) else "-" for a in ARMS]
        print(f"| {q} | {g} | " + " | ".join(cells) + " |")

print("\n## Hypotheses\n")
print("| # | comparison | treatment | none | one-sided Fisher p | supported |\n| --- | --- | --- | --- | --- | --- |")


def test(label, name, treat, ctrl, key="passed"):
    a, n1 = sum(r[key] is True for r in treat), len(treat)
    c, n2 = sum(r[key] is True for r in ctrl), len(ctrl)
    p = fisher_greater(a, n1, c, n2)
    print(f"| {label} | {name} | {a}/{n1} | {c}/{n2} | {p:.3f} | {'yes' if p < 0.05 else 'no'} |")


hard = ["BUG", "CROSS"]
test("H1", "superpowers pass, BUG+CROSS, both agents", sel(arm="superpowers", q=hard), sel(arm="none", q=hard))
test("H2", "pocock pass, BUG+CROSS, both agents", sel(arm="pocock", q=hard), sel(arm="none", q=hard))
test("H7", "pstack pass, all tasks, Cursor", sel(arm="pstack", agent="cursor"), sel(arm="none", agent="cursor"))
test("(ctrl)", "placebo pass, BUG+CROSS, both agents", sel(arm="placebo", q=hard), sel(arm="none", q=hard))
if BITE:
    for a in ["superpowers", "pocock", "pstack"]:
        ctrl = sel(arm="none", q="BUG")
        tr = sel(arm=a, q="BUG")
        for r in ctrl + tr:
            r["bites"] = r["bite"] == "bites"
        test("H4", f"{a}: BUG runs with a test that bites", tr, ctrl, "bites")
for a in ["superpowers", "pocock", "pstack", "placebo"]:
    agents = list({r["agent"] for r in sel(arm=a)})
    test("H5", f"{a}: test-file-first, share of all change runs", sel(arm=a), sel(arm="none", agent=agents), "test_first")
for a in ["superpowers", "pocock", "pstack", "placebo"]:
    chg = [r for r in sel(arm=a) if r["test_first"] is not None]
    ctrl = [r for r in sel(arm="none", agent=list({r["agent"] for r in sel(arm=a)})) if r["test_first"] is not None]
    test("(H5b)", f"{a}: test-file-first, only runs that edited both test and main", chg, ctrl, "test_first")

print("\n## Per arm and agent (all tasks)\n")
print("| agent | arm | pass | median tokens | tokens vs none | mean $ | skill read | added tests | test-file-first | overclaims | median diff lines | median s |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for g in ["codex", "cursor"]:
    base = {q: statistics.median(r["tokens"] for r in sel(agent=g, arm="none", q=q)) for q in ["BUG", "CROSS", "FEAT"]}
    for a in ARMS:
        rs = sel(agent=g, arm=a)
        if not rs:
            continue
        rel = statistics.median(r["tokens"] / base[r["q"]] for r in rs)
        tf = [r for r in rs if r["test_first"] is not None]
        print(f"| {g} | {a} | {frac(rs, 'passed')} | {statistics.median(r['tokens'] for r in rs)/1e6:.2f}M | {rel:.2f}x | "
              f"{statistics.mean(r['cost'] for r in rs):.3f} | {frac(rs, 'skill_read')} | {frac(rs, 'added_tests')} | "
              f"{sum(r['test_first'] for r in tf)}/{len(tf)} | {sum(r['overclaim'] for r in rs)} | "
              f"{statistics.median(r['diff_lines'] for r in rs):.0f} | {statistics.median(r['seconds'] for r in rs):.0f} |")

print("\n## Per cell detail\n")
print("| task | agent | arm | pass | hidden pass | other failures (runs) | overclaims | skill read | mean $ |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for q in ["BUG", "CROSS", "FEAT"]:
    for g in ["codex", "cursor"]:
        for a in ARMS:
            rs = sel(q=q, agent=g, arm=a)
            if rs:
                print(f"| {q} | {g} | {a} | {frac(rs, 'passed')} | {frac(rs, 'hidden_pass')} | "
                      f"{sum(1 for r in rs if r['other_failures'])} | {sum(r['overclaim'] for r in rs)} | "
                      f"{frac(rs, 'skill_read')} | {statistics.mean(r['cost'] for r in rs):.3f} |")
print(f"\nTotal spend: ${sum(r['cost'] for r in rows):.2f} (codex ${sum(r['cost'] for r in sel(agent='codex')):.2f}, "
      f"cursor ${sum(r['cost'] for r in sel(agent='cursor')):.2f} with no cache discount, as in the design)")
