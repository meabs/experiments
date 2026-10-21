"""Caveman analysis (Codex). Usage: python3 -I analyse.py <runs dir> > results/analysis.md

Relative cost follows the rig's method: each run's tokens are divided by the `none` mean for the same task, and the
interval is a percentile bootstrap (10,000 resamples within each task and arm, fixed seed) of the mean ratio.
"""
import glob, json, os, random, re, statistics as st, sys

RUNS = sys.argv[1]
TASKS = ["QA", "BUG", "FEAT"]
rows = []
for f in sorted(glob.glob(os.path.join(RUNS, "*/*/codex/*/run.json"))):
    rd = os.path.dirname(f)
    q, arm = rd.split(os.sep)[-4:-2]
    d = json.load(open(f))
    s = json.load(open(os.path.join(rd, "verify-summary.json")))
    words = re.findall(r"[A-Za-z']+", d["answer"].split("VERIFICATION")[0])
    t = d["tokens"]
    rows.append(dict(q=q, arm=arm, status=d["status"], passed=bool(s["pass"]), f1=s.get("mean_f1"), total=t["total"],
                     output=t["output"], fresh=t["input"] - t["cache_read"], cached=t["cache_read"], words=len(words),
                     articles=100 * sum(w.lower() in ("a", "an", "the") for w in words) / max(1, len(words)),
                     seconds=d["seconds"], turns=d["turns"],
                     cost=((t["input"] - t["cache_read"]) * 0.20 + t["cache_read"] * 0.02 + t["output"] * 1.20) / 1e6))


def sel(**kw):
    return [r for r in rows if all(r[k] == v for k, v in kw.items())]


def rel_ci(key, tasks):
    rng = random.Random(1)
    base = {q: st.mean(r[key] for r in sel(q=q, arm="none")) for q in tasks}
    groups = [[r[key] / base[q] for r in sel(q=q, arm="caveman")] for q in tasks]
    point = st.mean(x for g in groups for x in g)
    boots = []
    for _ in range(10000):
        b = {q: st.mean(rng.choice([r[key] for r in sel(q=q, arm="none")]) for _ in range(6)) for q in tasks}
        xs = [rng.choice([r[key] for r in sel(q=q, arm="caveman")]) / b[q] for q in tasks for _ in range(6)]
        boots.append(st.mean(xs))
    boots.sort()
    return point, boots[250], boots[9749]


print("# Caveman: analysis (Codex)\n")
print(f"{len(rows)} runs, statuses: {sorted({r['status'] for r in rows})}.\n")
print("| task | arm | pass | QA mean F1 | median total tokens | median output tokens | median reply words | median articles per 100 words | median s | mean $ |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for q in TASKS:
    for a in ["none", "caveman"]:
        rs = sel(q=q, arm=a)
        f1 = f"{st.mean(r['f1'] for r in rs):.3f}" if q == "QA" else "-"
        print(f"| {q} | {a} | {sum(r['passed'] for r in rs)}/{len(rs)} | {f1} | {st.median(r['total'] for r in rs) / 1e3:.0f}k | "
              f"{st.median(r['output'] for r in rs) / 1e3:.1f}k | {st.median(r['words'] for r in rs):.0f} | "
              f"{st.median(r['articles'] for r in rs):.1f} | {st.median(r['seconds'] for r in rs):.0f} | {st.mean(r['cost'] for r in rs):.3f} |")
print("\n## Hypotheses (preregistered, Codex only)\n")
print("| # | measure | caveman relative to none (95% CI) | rule | result |\n| --- | --- | --- | --- | --- |")
o = rel_ci("output", TASKS)
t = rel_ci("total", TASKS)
print(f"| C1 | output tokens | {o[0]:.2f} ({o[1]:.2f} to {o[2]:.2f}) | interval entirely below 1.00 | {'supported' if o[2] < 1 else 'not supported'} |")
print(f"| C2 | total tokens | {t[0]:.2f} ({t[1]:.2f} to {t[2]:.2f}) | interval entirely below 0.80 | {'supported' if t[2] < 0.8 else 'not supported'} |")
pc, pn = sum(r["passed"] for r in sel(arm="caveman")), sum(r["passed"] for r in sel(arm="none"))
print(f"| C3 | pass rate | {pc}/18 vs {pn}/18 | not lower by more than 3 of 18 | {'holds' if pn - pc <= 3 else 'fails'} |")
print("\nPer task (exploratory):\n")
print("| task | output, relative (95% CI) | total, relative (95% CI) |\n| --- | --- | --- |")
for q in TASKS:
    o, t = rel_ci("output", [q]), rel_ci("total", [q])
    print(f"| {q} | {o[0]:.2f} ({o[1]:.2f} to {o[2]:.2f}) | {t[0]:.2f} ({t[1]:.2f} to {t[2]:.2f}) |")
share = st.mean(r["output"] / r["total"] for r in sel(arm="none"))
print(f"\nOutput is {share * 100:.1f}% of a `none` run's total tokens on average, so even removing all output would cut "
      f"the total by about that much.\n")
print(f"Total spend: ${sum(r['cost'] for r in rows):.2f} (list-price estimate).")
