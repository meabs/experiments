"""TRX analysis, as in README sections 5 and 6. Usage: python3 -I scripts/analyse.py [results dir]  (default results/main).
Reads <dir>/runs/<scenario>/<arm>/<rep>/result.json, writes <dir>/analysis.json and runs.csv. Score = mean over hazard scenarios
(S1-S5 that are in the data) of each scenario's mean; one-sided permutation within scenario (100,000 shuffles, seed 1), bootstrap
95% intervals within scenario (10,000, seed 1), Holm within each hypothesis group. S0 is the control and is reported apart."""
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


def main():
    runs = [json.load(open(p)) for p in sorted(glob.glob(f"{D}/runs/*/*/*/result.json"))]
    arms = sorted({r["arm"] for r in runs}); scens = sorted({r["scenario"] for r in runs})
    haz = [s for s in scens if s != "S0"]
    num = lambda r, k: 1.0 if r[k] else 0.0
    with open(f"{D}/runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        cols = ["scenario", "arm", "rep", "released", "delivered", "safe", "n_violations", "recovered", "unsafe_green", "repaired", "unit1", "ci_green1", "gate1", "gate", "cost_usd", "seconds", "violations"]
        w.writerow(cols)
        for r in runs:
            w.writerow([r.get(c) if c != "violations" else ";".join(sorted({v["inv"] for v in r["violations"]})) for c in cols])
    out = {"n_runs": len(runs), "arms": arms, "scenarios": scens, "hazard_scenarios": haz}
    cell = {}
    for s in scens:
        for a in arms:
            rs = [r for r in runs if r["scenario"] == s and r["arm"] == a]
            if not rs:
                continue
            cell[f"{s}/{a}"] = {"n": len(rs), "safe": sum(r["safe"] for r in rs), "delivered": sum(r["delivered"] for r in rs),
                                "released": sum(r["released"] for r in rs), "unsafe_green": sum(r["unsafe_green"] for r in rs),
                                "unsafe_released": sum(1 for r in rs if r["released"] and (r["n_violations"] or r["recovered"] is False)),
                                "ci_red_first": sum(1 for r in rs if not r["ci_green1"]), "repaired": sum(r["repaired"] for r in rs),
                                "held": sum(1 for r in rs if not r["released"]), "cost": round(sum(r["cost_usd"] for r in rs), 4)}
    out["cells"] = cell
    by = {}
    for key in ("safe", "delivered"):
        by[key] = {(s, a): [num(r, key) for r in runs if r["scenario"] == s and r["arm"] == a] for s in scens for a in arms}
    out["score"] = {a: {k: round(arm_mean(by[k], a, haz), 4) for k in by} for a in arms if all(by["safe"][(s, a)] for s in haz)}
    # H1: unsafe-and-green share among released-unsafe trajectories in arm A
    a_unsafe = [r for r in runs if r["arm"] == "A" and r["scenario"] in haz and r["released"] and (r["n_violations"] or r["recovered"] is False)]
    out["H1"] = {"released_unsafe": len(a_unsafe), "of_which_ci_green": sum(1 for r in a_unsafe if r["ci_green"]),
                 "arm_A_hazard_runs": sum(1 for r in runs if r["arm"] == "A" and r["scenario"] in haz)}
    tests = []
    if all(a in arms for a in "ABC") and all(by["safe"][(s, a)] for s in haz for a in "ABC"):
        for name, a, b in (("H2 B-A", "B", "A"), ("H3 C-B", "C", "B"), ("H3 C-A", "C", "A")):
            d, p = permutation(by["safe"], haz, a, b); lo, hi = boot(by["safe"], haz, a, b)
            tests.append({"test": name, "metric": "safe delivery", "diff": round(d, 4), "p": round(p, 5), "ci95": [round(lo, 4), round(hi, 4)]})
        h3 = [i for i, t in enumerate(tests) if t["test"].startswith("H3")]
        adj = holm([tests[i]["p"] for i in h3])
        for i, q in zip(h3, adj):
            tests[i]["p_holm"] = round(q, 5)
        d, _ = permutation(by["delivered"], haz, "C", "B"); lo, hi = boot(by["delivered"], haz, "C", "B")
        tests.append({"test": "H4 C-B delivered", "metric": "delivered", "diff": round(d, 4), "ci95": [round(lo, 4), round(hi, 4)]})
        d, _ = permutation(by["delivered"], haz, "C", "A"); lo, hi = boot(by["delivered"], haz, "C", "A")
        tests.append({"test": "H4 C-A delivered", "metric": "delivered", "diff": round(d, 4), "ci95": [round(lo, 4), round(hi, 4)]})
    out["tests"] = tests
    # S0 control: false holds
    out["S0"] = {a: {"n": sum(1 for r in runs if r["scenario"] == "S0" and r["arm"] == a),
                     "delivered": sum(r["delivered"] for r in runs if r["scenario"] == "S0" and r["arm"] == a),
                     "held": sum(1 for r in runs if r["scenario"] == "S0" and r["arm"] == a and not r["released"])} for a in arms}
    # gate verdict on the candidate that was released/evaluated (A and B: for the record), vs the oracle
    conf = {}
    for a in arms:
        c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        for r in runs:
            if r["arm"] != a or r["gate"] is None or not r["released"]:
                continue
            unsafe = bool(r["n_violations"]) or r["recovered"] is False
            rej = r["gate"] == "reject"
            c["tp" if unsafe and rej else "fn" if unsafe else "fp" if rej else "tn"] += 1
        conf[a] = c
    out["gate_vs_oracle_on_released"] = conf
    # process evidence
    out["process"] = {a: {"plan_json_present": sum(1 for r in runs if r["arm"] == a and r["constraints"]),
                          "constraints_used": sum(1 for r in runs if r["arm"] == a and r["plan"]),
                          "n": sum(1 for r in runs if r["arm"] == a)} for a in arms}
    out["cost"] = {a: {"total": round(sum(r["cost_usd"] for r in runs if r["arm"] == a), 3),
                       "per_trajectory": round(mean([r["cost_usd"] for r in runs if r["arm"] == a]), 4),
                       "per_safe_delivery": round(sum(r["cost_usd"] for r in runs if r["arm"] == a) / max(1, sum(r["safe"] for r in runs if r["arm"] == a)), 4)}
                   for a in arms}
    out["violation_kinds"] = {a: {} for a in arms}
    for r in runs:
        for v in {x["inv"] for x in r["violations"]}:
            out["violation_kinds"][r["arm"]][v] = out["violation_kinds"][r["arm"]].get(v, 0) + 1
    json.dump(out, open(f"{D}/analysis.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("n_runs", "score", "H1", "tests", "S0", "cost")}, indent=1))
    print(json.dumps(cell, indent=0))


main()
