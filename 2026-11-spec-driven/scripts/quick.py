"""Quick look at SDD main results: share of hidden tests passed (per run, tickets equal), tokens, toolkit use.
Exploratory summary only; the pre-registered analysis (Holm-adjusted intervals) comes next."""
import collections, glob, json, os, random, re, statistics as st
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "main")
data = {}
for a in "VDLRSO":
    for f in glob.glob(f"{R}/{a}/runs/*/{a}/codex/*/run.json"):
        r = json.load(open(f)); d = os.path.dirname(f); v = json.load(open(d + "/verify-summary.json"))
        n = v["hidden_expected"]; ok = sum(1 for x in v["cases"].values() if x in ("pass", "passed", True, "PASS"))
        txt = " ".join(t.get("text", "") for t in r["tool_calls"])
        data.setdefault(a, {}).setdefault(r["question"], []).append(
            dict(share=ok / n, full=bool(v["pass"]), tok=r["tokens"]["total"], sec=r["seconds"],
                 speck=bool(re.search("speckit", txt)), ospec=bool(re.search("openspec", txt)),
                 notes=bool(re.search("notes/", txt)), claimed=None))
def arm_mean(a, key="share"):
    return st.mean(st.mean(x[key] for x in rs) for rs in data[a].values())
print("states seen:", collections.Counter(x for a in "V" for q in [0] for x in
      json.load(open(glob.glob(f"{R}/V/runs/*/V/codex/1/verify-summary.json")[0]))["cases"].values()))
print(f"{'arm':3} {'share':>6} {'full':>5} {'tokM':>6} {'sec':>5}")
for a in "VDLRSO":
    allr = [x for rs in data[a].values() for x in rs]
    print(f"{a:3} {arm_mean(a):6.1%} {sum(x['full'] for x in allr):>2}/30 {st.mean(x['tok'] for x in allr)/1e6:6.2f} {st.mean(x['sec'] for x in allr):5.0f}")
print("per ticket share:")
Q = sorted(data["V"])
print(" " * 15 + " ".join(f"{a:>5}" for a in "VDLRSO"))
for q in Q:
    print(f"{q:15}" + " ".join(f"{st.mean(x['share'] for x in data[a][q]):5.0%}" for a in "VDLRSO"))
print("toolkit use: S runs touching speckit", sum(x['speck'] for rs in data['S'].values() for x in rs), "/30;",
      "O runs touching openspec", sum(x['ospec'] for rs in data['O'].values() for x in rs), "/30;",
      "R runs writing notes/", sum(x['notes'] for rs in data['R'].values() for x in rs), "/30")
# paired bootstrap over runs within ticket (exploratory, unadjusted): difference in arm mean vs V and vs D
random.seed(1)
def diff(a, b, B=4000):
    ds = []
    for _ in range(B):
        ma = st.mean(st.mean(random.choices([x['share'] for x in data[a][q]], k=5)) for q in Q)
        mb = st.mean(st.mean(random.choices([x['share'] for x in data[b][q]], k=5)) for q in Q)
        ds.append(ma - mb)
    ds.sort(); return arm_mean(a) - arm_mean(b), ds[int(.025 * B)], ds[int(.975 * B)]
for b in "VD":
    for a in "DLRSO":
        if a != b:
            m, lo, hi = diff(a, b); print(f"{a} - {b}: {m*100:+.1f} pts  [{lo*100:+.1f}, {hi*100:+.1f}] (unadjusted bootstrap)")
