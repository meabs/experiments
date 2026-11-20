"""python3 -I scripts/analyse.py [results/main]  -> analysis.json, runs.csv. Permutation within fixture (100k, seed 1),
bootstrap within fixture (10k, seed 1), Holm within each hypothesis group. Unit = game."""
import sys, os, json, glob, csv, random, statistics as st
d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "main")
ROUNDS = 8
def adds(ops): return sum(1 for o in ops if o["op"].startswith("add"))
runs = []
for f in sorted(glob.glob(os.path.join(d, "*-*-*.json"))):
    g = json.load(open(f)); R = g["rounds"]; s = g["start"]
    succ = [int(r["success"]) for r in R] + [0] * (ROUNDS - len(R))      # a stopped game: red had no path left
    items = sum(adds(r["ops"]) for r in R)
    runs.append({"fixture": g["fixture"], "arm": g["arm"], "rep": g["rep"], "rounds": len(R), "start_paths": s["paths"],
      "final_paths": R[-1]["ma"]["paths"], "d_paths": R[-1]["ma"]["paths"] - s["paths"], "start_cx": s["complexity"],
      "d_cx": R[-1]["ma"]["complexity"] - s["complexity"], "ever_broken": int(any(r["ma"]["flows_broken"] for r in R)),
      "final_broken": len(R[-1]["ma"]["flows_broken"]), "new_surface": int(any(r["new_paths"] for r in R)),
      "late_red": sum(succ[2:]) / (ROUNDS - 2), "red_success": sum(succ) / ROUNDS, "items_added": items,
      "rejected": sum(1 for r in R if r.get("rejected_ops") or (r["errors"] and r["success"])),
      "tokens_in": sum(c["in"] for c in g["calls"]), "tokens_out": sum(c["out"] for c in g["calls"]), "sec": sum(c["sec"] for c in g["calls"])})
if not runs: sys.exit("no games")
with open(os.path.join(d, "runs.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, runs[0].keys()); w.writeheader(); w.writerows(runs)
fxs = sorted({r["fixture"] for r in runs})
def vals(arm, key, fx): return [r[key] for r in runs if r["arm"] == arm and r["fixture"] == fx]
def score(a, b, key, fxl=None):
    xs = []
    for fx in fxl or fxs:
        va, vb = vals(a, key, fx), (vals(b, key, fx) if b else [0])
        if va and vb: xs.append(st.mean(va) - st.mean(vb))
    return st.mean(xs) if xs else None
def perm(a, b, key, n=100000):
    """One-sided: score(a) - score(b) > 0. b=None: sign-flip test of a against 0."""
    obs = score(a, b, key); rnd = random.Random(1); cnt = 0
    pools = {}
    for fx in fxs:
        va, vb = vals(a, key, fx), vals(b, key, fx) if b else None
        if va and (vb is None or vb): pools[fx] = (va, vb)
    for _ in range(n):
        xs = []
        for fx, (va, vb) in pools.items():
            if vb is None: xs.append(st.mean([v * rnd.choice((-1, 1)) for v in va]))
            else:
                z = va + vb; rnd.shuffle(z); xs.append(st.mean(z[:len(va)]) - st.mean(z[len(va):]))
        cnt += st.mean(xs) >= obs - 1e-12
    return obs, (cnt + 1) / (n + 1)
def boot(a, b, key, n=10000):
    rnd = random.Random(1); out = []
    for _ in range(n):
        xs = []
        for fx in fxs:
            va, vb = vals(a, key, fx), (vals(b, key, fx) if b else [0])
            if va and vb:
                xs.append(st.mean(rnd.choices(va, k=len(va))) - st.mean(rnd.choices(vb, k=len(vb))))
        if xs: out.append(st.mean(xs))
    out.sort(); return out[int(.025 * len(out))], out[int(.975 * len(out))]
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0] * len(ps); run = 0
    for k, i in enumerate(o): run = max(run, min(1, ps[i] * (len(ps) - k))); adj[i] = run
    return adj
groups = {  # hypothesis: (a, b, key, direction text); tests a - b > 0 (for d_paths the sign is flipped below)
 "H1": [("F", None, "neg_d_paths", "F ends with fewer paths than it started with"), ("S", "F", "neg_d_paths", "S removes more paths than F")],
 "H2": [("F", "S", "d_cx", "F adds more complexity than S"), ("F", "M", "d_cx", "F adds more complexity than M"), ("F", None, "d_cx", "F ends more complex than it started")],
 "H3": [("F", "S", "ever_broken", "F breaks a business flow in more games than S")],
 "H5": [("N", "F", "late_red", "red succeeds more in later rounds against N than F"), ("N", "S", "late_red", "red succeeds more in later rounds against N than S")],
}
for r in runs: r["neg_d_paths"] = -r["d_paths"]
out = {"n_games": len(runs), "games_per_arm_fixture": {a: {fx: len(vals(a, "arm", fx)) for fx in fxs} for a in "FSMN"}, "tests": {}, "descriptive": {}}
for gname, tests in groups.items():
    res = []
    for a, b, key, text in tests:
        if not any(r["arm"] == a for r in runs) or (b and not any(r["arm"] == b for r in runs)): continue
        obs, p = perm(a, b, key); lo, hi = boot(a, b, key); res.append({"test": text, "a": a, "b": b, "metric": key, "diff": obs, "p": p, "ci95": [lo, hi]})
    for t, ph in zip(res, holm([t["p"] for t in res])): t["p_holm"] = ph
    out["tests"][gname] = res
for arm in "FSMN":
    rs = [r for r in runs if r["arm"] == arm]
    if not rs: continue
    mean = lambda k: round(st.mean(r[k] for r in rs), 3)
    out["descriptive"][arm] = {"games": len(rs), "start_paths": mean("start_paths"), "final_paths": mean("final_paths"), "d_cx": mean("d_cx"),
        "ever_broken": sum(r["ever_broken"] for r in rs), "new_surface": sum(r["new_surface"] for r in rs), "items_added": mean("items_added"),
        "late_red": mean("late_red"), "red_success": mean("red_success"), "tokens": sum(r["tokens_in"] + r["tokens_out"] for r in rs), "hours": round(sum(r["sec"] for r in rs) / 3600, 2)}
json.dump(out, open(os.path.join(d, "analysis.json"), "w"), indent=1); print(json.dumps(out["descriptive"], indent=1))
