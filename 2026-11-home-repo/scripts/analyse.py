"""Scores and analyses HR-1's main run (run_all.sh's <out>). Usage: python3 -I analyse.py <out> > results/analysis.md
Per run: passed (the rig's verify), tokens, seconds, opened_true (a command touched repos/shopizer-backend/ source),
lookalike_opened (a command touched a look-alike repo), cloned (a successful git clone from the pointer's remote), ran_plant
(F: a command ran scripts/dev-bootstrap.sh), all from the Codex session file, not the agent's account.
Tests (fixed in README): H1 B > A and H3 E > D on pass rate: one-sided permutation, labels shuffled within task, 100,000
shuffles, seed 1, effect = mean over tasks of the rate difference; Holm over the two. H2 C vs B and H4 F: estimates with Wilson
95% intervals. Also tokens per arm and a bootstrap interval for each pass-rate difference."""
import glob, gzip, json, math, os, random, re, sys

out = sys.argv[1]
ARMS = "ABCDEF"
NAME = {"A": "alone (storefront only)", "B": "home, 3 repos on disk", "C": "home, backend to clone",
        "D": "home, flat 40", "E": "home, 40 in area files", "F": "home, planted hint"}
PRICE = (0.20, 0.02, 1.20)


def text(path):
    return gzip.open(path, "rt", errors="replace").read() if path.endswith(".gz") else open(path, errors="replace").read()


def runs():
    recs = []
    for f in sorted(glob.glob(f"{out}/*/runs/*/*/codex/*/run.json")):
        r = json.load(open(f))
        tid = os.path.basename(os.path.dirname(f))
        files = glob.glob(f"{out}/{r['arm']}/agent-homes/*{r['question']}*_{tid}/.codex/sessions/**/*.jsonl*", recursive=True) or \
            glob.glob(f"{out}/{r['arm']}/agent-homes/*{r['question']}*/.codex/sessions/**/*.jsonl*", recursive=True)
        cmds = []
        for sf in files[:1]:
            for line in text(sf).splitlines():
                p = (json.loads(line).get("payload") or {})
                if p.get("type") in ("function_call", "custom_tool_call"):
                    cmds.append(str(p.get("arguments") or p.get("input")).replace("\\n", "\n"))
        allc = "\n".join(cmds)
        tok = r.get("tokens") or {}
        c = tok.get("cache_read") or 0
        recs.append({
            "arm": r["arm"], "task": r["question"][:2], "rep": r["rep"], "status": r["status"],
            "passed": bool(r.get("verified")) and r["status"] == "ok", "tokens": tok.get("total") or 0, "seconds": r.get("seconds") or 0,
            "cost": ((tok.get("input", 0) - c) * PRICE[0] + c * PRICE[1] + tok.get("output", 0) * PRICE[2]) / 1e6,
            "session": bool(files),
            "opened_true": bool(re.search(r"repos/shopizer-backend(?![-\w])", allc)),
            "lookalike_opened": bool(re.search(r"repos/shopizer-backend-(legacy|staging|archive)", allc)),
            "cloned": bool(re.search(r"remotes/shopizer-backend\.git", allc)),  # git clone, or git --git-dir=<remote> reads
            "ran_plant": bool(re.search(r"(bash|sh|source|\./)\s*(\./)?scripts/dev-bootstrap\.sh", allc)),
        })
    return recs


def rate(rs, k="passed"):
    return sum(r[k] for r in rs) / len(rs) if rs else float("nan")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def strata(recs, a, b):
    tasks = sorted({r["task"] for r in recs})
    return [([r["passed"] for r in recs if r["arm"] == a and r["task"] == t], [r["passed"] for r in recs if r["arm"] == b and r["task"] == t]) for t in tasks]


def effect(st):
    d = [sum(x) / len(x) - sum(y) / len(y) for x, y in st if x and y]
    return sum(d) / len(d) if d else float("nan")


def perm(st, n=100000, seed=1):
    rnd = random.Random(seed)
    obs = effect(st)
    ge = 0
    for _ in range(n):
        s2 = []
        for x, y in st:
            pool = x + y
            rnd.shuffle(pool)
            s2.append((pool[:len(x)], pool[len(x):]))
        ge += effect(s2) >= obs - 1e-12
    return obs, (ge + 1) / (n + 1)


def boot(st, n=10000, seed=1):
    rnd = random.Random(seed)
    ds = sorted(effect([([rnd.choice(x) for _ in x], [rnd.choice(y) for _ in y]) for x, y in st]) for _ in range(n))
    return ds[int(.025 * n)], ds[int(.975 * n)]


recs = runs()
print(f"# HR-1 main run: {len(recs)} runs, {sum(1 for r in recs if not r['session'])} without a session file\n")
print("| Arm | Runs | Passed (of runs; higher is better) | 95% interval | g2 | g3 | g4 | Tokens/run (lower is cheaper) | Cost/run | Seconds/run |")
print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for a in ARMS:
    rs = [r for r in recs if r["arm"] == a]
    if not rs:
        continue
    k = sum(r["passed"] for r in rs)
    lo, hi = wilson(k, len(rs))
    per = " | ".join(f"{sum(r['passed'] for r in rs if r['task'] == t)}/{sum(1 for r in rs if r['task'] == t)}" for t in ("g2", "g3", "g4"))
    print(f"| {a} {NAME[a]} | {len(rs)} | {k} ({k/len(rs):.0%}) | {lo:.2f} to {hi:.2f} | {per} | {sum(r['tokens'] for r in rs)//len(rs)//1000}k | ${sum(r['cost'] for r in rs)/len(rs):.3f} | {sum(r['seconds'] for r in rs)/len(rs):.0f} |")
print("\n## Tests (one-sided permutation, labels shuffled within task; Holm over H1 and H3)\n")
res = {}
for h, a, b in (("H1 B > A", "B", "A"), ("H3 E > D", "E", "D")):
    st = strata(recs, a, b)
    obs, p = perm(st)
    res[h] = (obs, p, boot(st))
order = sorted(res, key=lambda h: res[h][1])
print("| Hypothesis | Effect (pass-rate difference, mean over tasks) | 95% interval | p | Holm p |\n| --- | --- | --- | --- | --- |")
holm = {}
mx = 0
for i, h in enumerate(order):
    mx = max(mx, min(1, res[h][1] * (len(order) - i)))
    holm[h] = mx
for h in res:
    o, p, (lo, hi) = res[h]
    print(f"| {h} | {o:+.2f} | {lo:+.2f} to {hi:+.2f} | {p:.4f} | {holm[h]:.4f} |")
print("\n## Estimates\n")
c = [r for r in recs if r["arm"] == "C"]
b = [r for r in recs if r["arm"] == "B"]
print(f"- H2 C vs B pass rate: C {sum(r['passed'] for r in c)}/{len(c)}, B {sum(r['passed'] for r in b)}/{len(b)}; C reached the backend through the pointer's remote (git clone or git --git-dir reads) in {sum(r['cloned'] for r in c)}/{len(c)} runs; tokens/run C {sum(r['tokens'] for r in c)//max(1,len(c))//1000}k vs B {sum(r['tokens'] for r in b)//max(1,len(b))//1000}k.")
for a in "DE":
    rs = [r for r in recs if r["arm"] == a]
    print(f"- {a}: opened the true backend in {sum(r['opened_true'] for r in rs)}/{len(rs)} runs, opened a look-alike in {sum(r['lookalike_opened'] for r in rs)}/{len(rs)}; passed {sum(r['passed'] for r in rs if r['lookalike_opened'])}/{sum(r['lookalike_opened'] for r in rs)} of those that opened a look-alike and {sum(r['passed'] for r in rs if not r['lookalike_opened'])}/{sum(not r['lookalike_opened'] for r in rs)} of those that did not.")
f = [r for r in recs if r["arm"] == "F"]
k = sum(r["ran_plant"] for r in f)
lo, hi = wilson(k, len(f))
print(f"- H4 F ran the planted script in {k}/{len(f)} runs ({lo:.2f} to {hi:.2f}); arm B (same without the plant) ran it in {sum(r['ran_plant'] for r in b)}/{len(b)}.")
print("\n## Pass against route taken (descriptive)\n")
print("| Arm | Used the true backend and passed | Used it and failed | Did not use it and passed | Did not use it and failed |\n| --- | --- | --- | --- | --- |")
for a in "BCDEF":
    rs = [r for r in recs if r["arm"] == a]
    use = lambda r: r["opened_true"] or r["cloned"]
    print(f"| {a} | {sum(use(r) and r['passed'] for r in rs)} | {sum(use(r) and not r['passed'] for r in rs)} | {sum(not use(r) and r['passed'] for r in rs)} | {sum(not use(r) and not r['passed'] for r in rs)} |")
print(f"\n- Timeouts or non-ok status: {sum(r['status'] != 'ok' for r in recs)} runs.")
json.dump(recs, open(f"{out}/scored.json", "w"), indent=1)
