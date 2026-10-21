"""Analysis for skills-tasks, fixed before the measured runs (see README, "Hypotheses and analysis").

The unit is the task. For each task and arm, passes is 0 to 2. T1 and T2 compare each pack with `none` through the
per-task difference in passes: an exact one-sided sign-flip permutation test over tasks, Holm-adjusted across T1 and
T2. T3 (placebo) is two-sided and reported only. Effects are the mean per-task difference in pass rate with a
bootstrap interval over tasks (10,000 resamples, seed 1).

Usage: python3 -I analyse.py <runs dir> > results/analysis.md
"""
import glob, gzip, itertools, json, os, random, statistics as st, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-skills-impact", "scripts"))
import process  # noqa: E402  (test-file-first and TDD evidence, unchanged from skills-impact)
from stats import holm  # noqa: E402

RUNS = sys.argv[1]
ARMS = ["none", "placebo", "superpowers", "pocock"]
KIND = {"PAGE": "real bug", "CONTENT": "real bug", "AMBIG": "real bug", "AVAIL": "real bug", "ADDR": "real bug",
        "CUSTDUP": "real bug", "CUSTPAGE": "real bug", "NOTFOUND": "real bug", "MANINUSE": "real bug", "CATDUP": "real bug",
        "CARTCALC": "planted bug", "TAXRATE": "feature", "REVIEW": "feature", "CATCOUNT": "feature", "MANORDER": "feature",
        "CUSTSEARCH": "feature", "TAXPAGE": "feature",
        "HREVIEW": "real bug", "HCUST": "feature", "MANCODE": "feature"}


def cost(t):
    return ((t["input"] - t["cache_read"]) * 0.20 + t["cache_read"] * 0.02 + t["output"] * 1.20) / 1e6


rows = []
for f in sorted(glob.glob(os.path.join(RUNS, "*/*/codex/*/run.json"))):
    rd = os.path.dirname(f)
    task, arm = rd.split(os.sep)[-4:-2]
    d = json.load(open(f))
    sp = os.path.join(rd, "verify-summary.json")
    s = json.load(open(sp)) if os.path.exists(sp) else {"pass": False}
    raw = os.path.join(rd, "raw.out")
    fh = open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")
    ev = process.events_codex(fh)
    ns = [l.split("\t") for l in open(os.path.join(rd, "agent.numstat")).read().splitlines() if l.strip()]
    own = {os.path.basename(p)[:-5] for _, _, p in ns if "/src/test/" in p and p.endswith(".java")}
    claim = d.get("claim") if isinstance(d.get("claim"), dict) else {}
    rows.append(dict(task=task, arm=arm, status=d["status"], passed=bool(s.get("pass")) and d["status"] == "ok",
                     tokens=d["tokens"]["total"], cost=cost(d["tokens"]), seconds=d["seconds"],
                     skill=any(".agents/skills/" in (t.get("text") or "") and "SKILL.md" in (t.get("text") or "") for t in d.get("tool_calls") or []),
                     tff=process.test_file_first(ev), tdd=process.classify_tdd(ev, own)[0],
                     test_runs=sum(e["k"] == "test" for e in ev),
                     test_lines=sum(int(a) + int(b) for a, b, p in ns if a != "-" and "/src/test/" in p),
                     prod_lines=sum(int(a) + int(b) for a, b, p in ns if a != "-" and "/src/test/" not in p),
                     overclaim=claim.get("result") == "passed" and not s.get("pass")))

tasks = sorted({r["task"] for r in rows})
cell = defaultdict(list)
for r in rows:
    cell[(r["task"], r["arm"])].append(r)


def passes(t, a):
    return sum(r["passed"] for r in cell[(t, a)])


def signflip_p(diffs, two_sided=False):
    obs = sum(diffs)
    nz = [d for d in diffs if d]
    count = total = 0
    for signs in itertools.product((1, -1), repeat=len(nz)):
        s = sum(x * y for x, y in zip(nz, signs))
        total += 1
        count += (abs(s) >= abs(obs)) if two_sided else (s >= obs)
    return count / total if total else 1.0


def boot(values, n=10000):
    rng = random.Random(1)
    means = sorted(st.mean(rng.choice(values) for _ in values) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


print(f"# skills-tasks: analysis\n\n{len(rows)} runs over {len(tasks)} tasks; statuses: "
      f"{ {s: sum(r['status'] == s for r in rows) for s in sorted({r['status'] for r in rows})} }.\n")
print("## Passes per task (of 2)\n")
print("| task | kind | " + " | ".join(ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
for t in tasks:
    print(f"| {t} | {KIND.get(t, '?')} | " + " | ".join(str(passes(t, a)) for a in ARMS) + " |")
print("| **total** | | " + " | ".join(f"**{sum(passes(t, a) for t in tasks)}/{2 * len(tasks)}**" for a in ARMS) + " |")

print("\n## Hypotheses (preregistered)\n")
print("| # | pack vs none | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p | Holm p |")
print("| --- | --- | --- | --- | --- | --- |")
res = {}
for h, a, two in [("T1", "superpowers", False), ("T2", "pocock", False), ("T3", "placebo", True)]:
    d = [passes(t, a) - passes(t, "none") for t in tasks]
    rate = [x / 2 for x in d]
    res[h] = (a, d, st.mean(rate), boot(rate), signflip_p(d, two))
adj = dict(zip(["T1", "T2"], holm([res["T1"][4], res["T2"][4]])))
for h in ["T1", "T2", "T3"]:
    a, d, m, (lo, hi), p = res[h]
    tail = f"{p:.3f} | {adj[h]:.3f} |" if h in adj else f"{p:.3f} (two-sided) | - |"
    print(f"| {h} | {a} | {sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)} | "
          f"{m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | " + tail)
print("\nA pack's gain counts as a pack effect only if it exceeds the placebo's (T3).")

print("\n## Cost and process (all tasks)\n")
print("| arm | runs | mean tokens | per-task token ratio vs none (95% CI) | mean $ | median s | median Maven test runs | "
      "median production / test lines | skill read | test-file-first | confirmed TDD | unknown TDD | overclaims |")
print("| --- |" + " --- |" * 12)
for a in ARMS:
    rs = [r for r in rows if r["arm"] == a]
    ratios = [st.mean(r["tokens"] for r in cell[(t, a)]) / st.mean(r["tokens"] for r in cell[(t, "none")]) for t in tasks]
    lo, hi = boot(ratios)
    print(f"| {a} | {len(rs)} | {st.mean(r['tokens'] for r in rs) / 1e6:.2f}M | {st.mean(ratios):.2f} ({lo:.2f} to {hi:.2f}) | "
          f"{st.mean(r['cost'] for r in rs):.3f} | {st.median(r['seconds'] for r in rs):.0f} | {st.median(r['test_runs'] for r in rs):.0f} | "
          f"{st.median(r['prod_lines'] for r in rs):.0f} / {st.median(r['test_lines'] for r in rs):.0f} | "
          f"{sum(r['skill'] for r in rs)}/{len(rs)} | {sum(r['tff'] is True for r in rs)}/{len(rs)} | "
          f"{sum(r['tdd'] == 'tdd-confirmed' for r in rs)}/{len(rs)} | {sum(r['tdd'] == 'unknown' for r in rs)} | "
          f"{sum(r['overclaim'] for r in rs)} |")

print("\n## Exploratory: by kind of task\n")
print("| kind | tasks | " + " | ".join(ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
for k in ["real bug", "planted bug", "feature"]:
    ts = [t for t in tasks if KIND.get(t) == k]
    if ts:
        print(f"| {k} | {len(ts)} | " + " | ".join(f"{sum(passes(t, a) for t in ts)}/{2 * len(ts)}" for a in ARMS) + " |")
print(f"\nTotal estimated spend (list prices): ${sum(r['cost'] for r in rows):.2f}.")
