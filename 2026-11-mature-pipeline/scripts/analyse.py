"""TRX-2 analysis, README sections 5 and 6. Usage: python3 -I scripts/analyse.py [results dir] (default results/main).
Reads <dir>/runs/<scenario>/<arm>/<rep>/result.json, writes <dir>/analysis.json and runs.csv. Score = mean over hazard scenarios
(S1-S5 in the data) of each scenario's mean; one-sided permutation within scenario (100,000 shuffles, seed 1), bootstrap 95%
intervals within scenario (10,000, seed 1), Holm within each hypothesis group. S0 is the control and is reported apart."""
import csv, glob, json, os, random, sys
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[1] if len(sys.argv) > 1 else f"{E}/results/main"


def mean(x):
    return sum(x) / len(x) if x else float("nan")


def arm_mean(by, arm, fx):
    return mean([mean(by[(f, arm)]) for f in fx])


def permutation(by, fx, a, b, n=100_000, seed=1):
    rng = random.Random(seed)
    obs = arm_mean(by, a, fx) - arm_mean(by, b, fx)
    pools = {f: by[(f, a)] + by[(f, b)] for f in fx}; k = {f: len(by[(f, a)]) for f in fx}
    hit = 0
    for _ in range(n):
        d = 0.0
        for f in fx:
            p = pools[f][:]; rng.shuffle(p)
            d += mean(p[:k[f]]) - mean(p[k[f]:])
        hit += d / len(fx) >= obs - 1e-12
    return obs, (hit + 1) / (n + 1)


def boot(by, fx, a, b, n=10_000, seed=1):
    rng = random.Random(seed); ds = []
    for _ in range(n):
        d = 0.0
        for f in fx:
            xa = [rng.choice(by[(f, a)]) for _ in by[(f, a)]]; xb = [rng.choice(by[(f, b)]) for _ in by[(f, b)]]
            d += mean(xa) - mean(xb)
        ds.append(d / len(fx))
    ds.sort(); return ds[int(.025 * n)], ds[int(.975 * n) - 1]


def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0] * len(ps); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (len(ps) - r) * ps[i])); adj[i] = run
    return adj


METRICS = {  # per trajectory
    "safe": lambda r: 1.0 if r["safe"] else 0.0,
    "safe_first": lambda r: 1.0 if r["safe_first"] else 0.0,
    "delivered": lambda r: 1.0 if r["delivered"] else 0.0,
    "repairs": lambda r: float(r["repairs"]),
    "cost_usd": lambda r: r["cost_usd"],
    "seconds": lambda r: float(r["seconds"]),
    "any_false_hold": lambda r: 1.0 if r["false_holds"] else 0.0,
}


def main():
    runs = [json.load(open(p)) for p in sorted(glob.glob(f"{D}/runs/*/*/*/result.json"))]
    arms = sorted({r["arm"] for r in runs}); scens = sorted({r["scenario"] for r in runs})
    haz = [s for s in scens if s != "S0"]
    with open(f"{D}/runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        cols = ["scenario", "arm", "rep", "released", "delivered", "safe", "safe_first", "repairs", "false_holds", "safe_default_order", "n_violations", "recovered", "cost_usd", "seconds", "violations"]
        w.writerow(cols)
        for r in runs:
            w.writerow([r.get(c) if c != "violations" else ";".join(sorted({v["inv"] for v in r["violations"]})) for c in cols])
    out = {"n_runs": len(runs), "arms": arms, "scenarios": scens, "hazard_scenarios": haz}
    by = {m: {(s, a): [fn(r) for r in runs if r["scenario"] == s and r["arm"] == a] for s in scens for a in arms} for m, fn in METRICS.items()}
    cell = {}
    for s in scens:
        for a in arms:
            rs = [r for r in runs if r["scenario"] == s and r["arm"] == a]
            if rs:
                cell[f"{s}/{a}"] = {"n": len(rs), "safe": sum(r["safe"] for r in rs), "safe_first": sum(r["safe_first"] for r in rs),
                                    "delivered": sum(r["delivered"] for r in rs), "held_final": sum(1 for r in rs if r["held_final"]),
                                    "repairs": sum(r["repairs"] for r in rs), "false_holds": sum(r["false_holds"] for r in rs),
                                    "cost": round(sum(r["cost_usd"] for r in rs), 4)}
    out["cells"] = cell
    full = lambda a: all(by["safe"][(s, a)] for s in haz)
    out["score"] = {a: {m: round(arm_mean(by[m], a, haz), 4) for m in METRICS} for a in arms if full(a)}
    tests = []
    for m, hi_good in (("safe", True), ("safe_first", True), ("repairs", False), ("cost_usd", False), ("seconds", False)):
        for name, a, b in (("B-A", "B", "A"), ("C-B", "C", "B"), ("C-A", "C", "A")):
            if a in arms and b in arms and full(a) and full(b):
                if hi_good:
                    d, p = permutation(by[m], haz, a, b)
                else:
                    d, p = permutation(by[m], haz, b, a); d = -d   # one-sided: a lower than b
                lo, hi = boot(by[m], haz, a, b)
                tests.append({"test": name, "metric": m, "diff": round(d, 4), "p_one_sided": round(p, 5), "ci95": [round(lo, 4), round(hi, 4)]})
    for m in ("safe", "safe_first"):
        idx = [i for i, t in enumerate(tests) if t["metric"] == m]
        for i, q in zip(idx, holm([tests[i]["p_one_sided"] for i in idx])):
            tests[i]["p_holm"] = round(q, 5)
    out["tests"] = tests
    out["S0"] = {a: {"n": sum(1 for r in runs if r["scenario"] == "S0" and r["arm"] == a),
                     "safe": sum(r["safe"] for r in runs if r["scenario"] == "S0" and r["arm"] == a),
                     "false_holds": sum(r["false_holds"] for r in runs if r["scenario"] == "S0" and r["arm"] == a)} for a in arms}
    cands = {a: sum(len(r["rounds"]) for r in runs if r["arm"] == a) for a in arms}
    out["blocking"] = {a: {"candidates": cands[a], "held": sum(1 for r in runs if r["arm"] == a for e in r["rounds"] if e["held"]),
                           "false_holds": sum(r["false_holds"] for r in runs if r["arm"] == a)} for a in arms}
    out["plan_dependence_C"] = {"released_safe": sum(1 for r in runs if r["arm"] == "C" and r["safe"]),
                                "safe_only_with_plan": sum(1 for r in runs if r["arm"] == "C" and r["safe"] and not r["safe_default_order"])}
    out["first_candidate"] = {a: {"pipeline_pass_first": sum(1 for r in runs if r["arm"] == a and r["pipeline_pass_first"]),
                                  "oracle_safe_first_candidate": sum(1 for r in runs if r["arm"] == a and r["oracle_first_candidate_safe"]),
                                  "n": sum(1 for r in runs if r["arm"] == a)} for a in arms}
    out["cost"] = {a: {"total": round(sum(r["cost_usd"] for r in runs if r["arm"] == a), 3),
                       "per_trajectory": round(mean([r["cost_usd"] for r in runs if r["arm"] == a]), 4),
                       "per_safe_release": round(sum(r["cost_usd"] for r in runs if r["arm"] == a) / max(1, sum(r["safe"] for r in runs if r["arm"] == a)), 4)}
                   for a in arms}
    out["violation_kinds"] = {a: {} for a in arms}
    for r in runs:
        for v in {x["inv"] for x in r["violations"]}:
            out["violation_kinds"][r["arm"]][v] = out["violation_kinds"][r["arm"]].get(v, 0) + 1
    json.dump(out, open(f"{D}/analysis.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("n_runs", "score", "tests", "S0", "blocking", "first_candidate", "plan_dependence_C", "cost")}, indent=1))
    print(json.dumps(cell))


main()
