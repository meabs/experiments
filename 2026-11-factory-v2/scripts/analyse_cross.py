"""Run-level analysis of the 25 cross-pairs (README "Test"). No model is used here.
Pair score f[a][b] = share of votes (both judges, both orders) for factory run b over plain run a (tie = half).
Each run's win share: factory run b = mean over a of f[a][b]; plain run a = 1 - mean over b of f[a][b].
Statistic = mean win share of factory runs minus mean win share of plain runs (= 2 * mean pair score - 1).
Permutation: the 252 ways of calling 5 of the 10 runs "factory"; two-sided p = share of splits with |stat| >= observed.
Approximate, because win shares are not independent (they come from one 5 x 5 table). Bootstrap 95% interval: resample the
5 plain and the 5 factory runs with replacement (rows and columns), recompute the mean pair score. Per criterion and per
judge, descriptive. Usage: python3 -I analyse_cross.py <stage dir> -> analysis.md, analysis.json
"""
import itertools, json, random, sys
from pathlib import Path

CRIT = ["overall", "novelty", "fit", "plausible", "hierarchy", "polish", "identity"]


def load(stage, crop=False):
    rows = []
    for f in sorted(Path(stage).glob("cross-crop-*.jsonl" if crop else "cross-[!c]*.jsonl")):
        rows += [j for j in map(json.loads, f.open()) if "error" not in j]
    return rows


def vote(j, c):
    v = j[c]
    if v == "tie":
        return 0.5
    shown_first = j["first"]  # arm shown as Design 1
    fac = "1" if shown_first == "B" else "2"
    return 1.0 if v == fac else 0.0


def matrix(rows, c, judge=None):
    reps = (sorted({j["a"] for j in rows}), sorted({j["b"] for j in rows}))
    f = {}
    for j in rows:
        if judge and j["judge"] != judge:
            continue
        f.setdefault((j["a"], j["b"]), []).append(vote(j, c))
    return reps, {k: sum(v) / len(v) for k, v in f.items()}


def stat_and_p(reps, f):
    ra, rb = reps
    plain = [1 - sum(f[(a, b)] for b in rb) / len(rb) for a in ra]
    fac = [sum(f[(a, b)] for a in ra) / len(ra) for b in rb]
    runs = plain + fac
    obs = sum(fac) / len(fac) - sum(plain) / len(plain)
    cnt = tot = 0
    for idx in itertools.combinations(range(len(runs)), len(ra)):
        s = sum(runs[i] for i in idx) / len(idx) - sum(runs[i] for i in range(len(runs)) if i not in idx) / (len(runs) - len(idx))
        tot += 1
        cnt += abs(s) >= abs(obs) - 1e-12
    return obs, cnt / tot


def boot(reps, f, n=5000, seed=1):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        ra = [rnd.choice(reps[0]) for _ in reps[0]]
        rb = [rnd.choice(reps[1]) for _ in reps[1]]
        out.append(sum(f[(a, b)] for a in ra for b in rb) / (len(ra) * len(rb)))
    out.sort()
    return out[int(.025 * n)], out[int(.975 * n)]


def main(stage, crop=False, drop=None):
    rows = load(stage, crop)
    if drop:
        rows = [j for j in rows if j["b"] != drop]
    judges = sorted({j["judge"] for j in rows})
    res = {}
    lines = ["# FUT-1 cross-pair results" + (" (cropped re-score, exploratory)" if crop else " (uncropped captures, primary)"), "", f"{len(rows)} judge calls, judges: {', '.join(judges)}.", "",
             "Mean pair score = share of votes for the factory design over the 25 plain x factory pairs (0.5 = no preference; "
             "above 0.5 favours the factory, below 0.5 the plain agent). Obs = factory minus plain mean win share (= 2 x score - 1). "
             "p: permutation over the 252 splits of the 10 runs (approximate); interval: bootstrap over runs.", "",
             "| Criterion | Mean pair score (95% interval) | Obs | p | Pairs factory wins | plain wins | split | " + " | ".join(
                 j.split("/")[-1] for j in judges) + " |", "| --- | --- | --- | --- | --- | --- | --- | " + " | ".join("---" for _ in judges) + " |"]
    for c in CRIT:
        reps, f = matrix(rows, c)
        npairs = len({(j["a"], j["b"]) for j in rows}) if drop else 25
        if len(f) < npairs:
            lines.append(f"| {c} | incomplete ({len(f)} of 25 pairs) | | | | | | |")
            continue
        obs, p = stat_and_p(reps, f)
        lo, hi = boot(reps, f)
        m = sum(f.values()) / len(f)
        w = sum(v > .5 for v in f.values()); l = sum(v < .5 for v in f.values())
        per = []
        for jd in judges:
            _, fj = matrix(rows, c, jd)
            per.append(f"{sum(fj.values()) / len(fj):.2f}")
        res[c] = {"mean": m, "lo": lo, "hi": hi, "obs": obs, "p": p, "wins": [w, l, len(f) - w - l], "per_judge": per}
        lines.append(f"| {c} | {m:.2f} ({lo:.2f} to {hi:.2f}) | {obs:+.2f} | {p:.3f} | {w} | {l} | {len(f) - w - l} | " + " | ".join(per) + " |")
    # position bias
    lines += ["", "Judge position bias (share choosing the design shown first on 'overall'; same choice in both orders):", ""]
    for jd in judges:
        r = [j for j in rows if j["judge"] == jd]
        first = sum((j["overall"] == "1") for j in r) / max(1, len(r))
        pairs = {}
        for j in r:
            pairs.setdefault((j["a"], j["b"]), {})[j["first"]] = vote(j, "overall")
        same = sum(1 for d in pairs.values() if len(d) == 2 and d["A"] == d["B"]) / max(1, len(pairs))
        lines.append(f"- {jd}: first-shown {first:.0%}, same choice in both orders {same:.0%}")
    Path(stage, ("analysis-drop%s" % drop if drop else "analysis") + ("-crop" if crop else "") + ".md").write_text("\n".join(lines) + "\n")
    Path(stage, ("analysis-drop%s" % drop if drop else "analysis") + ("-crop" if crop else "") + ".json").write_text(json.dumps(res, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    d = sys.argv[sys.argv.index("--drop") + 1] if "--drop" in sys.argv else None
    main(sys.argv[1], "--crop" in sys.argv, d)
