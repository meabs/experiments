"""Analysis for swarm-tax, fixed before the measured runs (README, "Hypotheses and analysis").

Score per run: the share of the task's hidden tests passed (verify-summary.json "cases"; 0 if none ran). Arms are compared
by the mean over tasks of each task's mean score.

- H1 team > solo and H3 team-full > team: one-sided permutation tests, arm labels shuffled within each task (100,000
  shuffles, seed 1).
- H2 team vs solo-best-of-k: two-sided bootstrap within tasks (team and solo runs resampled, K recomputed; 10,000, seed 1).
- Holm over H1 to H3 at alpha 0.05. Effect intervals: bootstrap within tasks, 10,000 resamples, seed 1.

K (solo-best-of-k): attempts in random order, keep the first that passes the visible check (compiles, and the agent's own
tests pass if it wrote any), else the k-th. Over every ordering of a task's n solo runs this has a closed form: with m
runs passing the check, q = C(n-m, k) / C(n, k) is the chance none of the first k passes; then the kept run is uniform
over the passing runs with probability 1 - q, and uniform over the failing runs with probability q. k = round(mean cost of
the team arm / mean cost of solo), clamped to [2, 6].

Secondary: verified passes, cost and tokens (every session, from the Codex session files), wall time, cost per hidden test
passed, the rubber stamp rate, what the review caught, whether the team happened, false success claims.

Usage: python3 -I analyse.py <trial out dir> [<trial out dir> ...] > results/analysis.md
       (each dir holds runs/ and agent-homes/ from one trial file; sessions.json is written beside each run)
"""
import glob, json, math, os, random, statistics as st, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(E, "..", "2026-10-skills-impact", "scripts"))
from stats import holm  # noqa: E402

ARMS = ["solo", "team", "team-full"]
PERMS, BOOTS, SEED = 100_000, 10_000, 1


def hidden_count(task):
    n = 0
    for f in glob.glob(os.path.join(E, "hidden", task, "*.java")):
        n += sum(1 for line in open(f) if line.strip().startswith("@Test"))
    return n


def audit(out, rd, task, arm, rep):
    p = os.path.join(rd, "sessions.json")
    if not os.path.exists(p):
        tid = f"{task}_{arm}_codex_{rep}".lower().replace("-", "_")
        home = os.path.join(out, "agent-homes", tid, ".codex")
        clone = os.path.join(out, "work", task, arm, "codex", str(rep))
        if not os.path.isdir(home):
            return None
        with open(p, "w") as f:
            subprocess.run([sys.executable, "-I", os.path.join(HERE, "audit_run.py"), home, clone], stdout=f, check=True)
    return json.load(open(p))


def load(outs):
    runs = []
    for out in outs:
        for f in sorted(glob.glob(os.path.join(out, "runs", "*", "*", "codex", "*", "run.json"))):
            rd = os.path.dirname(f)
            task, arm, _, rep = rd.split(os.sep)[-4:]
            r = json.load(open(f))
            vs = os.path.join(rd, "verify-summary.json")
            v = json.load(open(vs)) if os.path.exists(vs) else {}
            n = hidden_count(task)
            passed = sum(1 for o in (v.get("cases") or {}).values() if o == "pass")
            vis = json.load(open(os.path.join(rd, "visible.json"))) if os.path.exists(os.path.join(rd, "visible.json")) else {}
            rel = json.load(open(os.path.join(rd, "relevance.json"))) if os.path.exists(os.path.join(rd, "relevance.json")) else {}
            own_ok = not str(rel.get("reason", "")).startswith(("its tests fail", "its tests did not compile"))
            s = audit(out, rd, task, arm, rep)
            runs.append({
                "task": task, "arm": arm, "rep": int(rep), "status": r.get("status"), "seconds": r.get("seconds") or 0,
                "score": passed / n if n else 0.0, "passed": passed, "n": n, "verified": bool(v.get("pass")),
                "visible": bool(vis.get("compiles")) and own_ok,
                "cost": s["cost"] if s else 0.0, "tokens": s["tokens"] if s else {}, "sessions": s,
                "claim_match": r.get("claim_match"),
            })
    return runs


def by_task(runs, arm):
    d = defaultdict(list)
    for r in runs:
        if r["arm"] == arm:
            d[r["task"]].append(r)
    return d


def k_estimate(solo, k):
    """Expected score of best-of-k over every ordering of these solo runs (closed form; see the module docstring)."""
    n = len(solo)
    if n == 0:
        return float("nan")
    k = min(k, n)
    good = [r["score"] for r in solo if r["visible"]]
    bad = [r["score"] for r in solo if not r["visible"]]
    m = len(good)
    q = math.comb(n - m, k) / math.comb(n, k) if n - m >= k else 0.0
    return (1 - q) * (st.mean(good) if good else 0.0) + q * (st.mean(bad) if bad else 0.0)


def arm_mean(groups, tasks):
    return st.mean(st.mean(r["score"] for r in groups[t]) for t in tasks)


def diff(ga, gb, tasks):
    return st.mean(st.mean(r["score"] for r in ga[t]) - st.mean(r["score"] for r in gb[t]) for t in tasks)


def permutation(ga, gb, tasks, rng):
    """One-sided p that arm a scores higher than arm b, labels shuffled within each task."""
    obs = diff(ga, gb, tasks)
    pools = {t: ([r["score"] for r in ga[t]] + [r["score"] for r in gb[t]], len(ga[t])) for t in tasks}
    hits = 0
    for _ in range(PERMS):
        tot = 0.0
        for t, (pool, na) in pools.items():
            p = pool[:]
            rng.shuffle(p)
            tot += st.fmean(p[:na]) - st.fmean(p[na:])
        if tot / len(tasks) >= obs - 1e-12:
            hits += 1
    return obs, (hits + 1) / (PERMS + 1)


def boot_ci(stat, rng):
    xs = sorted(stat(rng) for _ in range(BOOTS))
    return xs, xs[int(0.025 * BOOTS)], xs[int(0.975 * BOOTS) - 1]


def resample(g, rng):
    return {t: [rng.choice(rs) for _ in rs] for t, rs in g.items()}


def fmt(x, d=3):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def main(outs):
    runs = load(outs)
    g = {a: by_task(runs, a) for a in ARMS}
    tasks = sorted(set(g["solo"]) & set(g["team"]) & set(g["team-full"]))
    out = ["# swarm-tax: analysis", "", f"Runs: {len(runs)}; tasks with all three arms: {', '.join(tasks) or 'none'}.", ""]
    if not tasks:
        print("\n".join(out + ["No task has runs in all three arms."]))
        return

    cost = {a: st.mean(r["cost"] for r in runs if r["arm"] == a) for a in ARMS}
    kt = max(2, min(6, round(cost["team"] / cost["solo"]))) if cost["solo"] else 2
    kf = max(2, min(6, round(cost["team-full"] / cost["solo"]))) if cost["solo"] else 2
    K = {t: k_estimate(g["solo"][t], kt) for t in tasks}
    KF = {t: k_estimate(g["solo"][t], kf) for t in tasks}

    out += ["## Scores (share of hidden tests passed)", "",
            "| task | solo | team | team-full | best-of-k (k={}) | best-of-k (k={}) |".format(kt, kf), "| --- | --- | --- | --- | --- | --- |"]
    for t in tasks:
        out.append(f"| {t} | " + " | ".join(fmt(st.mean(r["score"] for r in g[a][t])) for a in ARMS)
                   + f" | {fmt(K[t])} | {fmt(KF[t])} |")
    out.append("| **mean over tasks** | " + " | ".join(fmt(arm_mean(g[a], tasks)) for a in ARMS)
               + f" | {fmt(st.mean(K.values()))} | {fmt(st.mean(KF.values()))} |")
    out += ["", f"k = round(mean cost of the team arm / mean cost of solo), in [2, 6]: team ${cost['team']:.3f} / solo "
            f"${cost['solo']:.3f} gives k = {kt}; team-full ${cost['team-full']:.3f} gives k = {kf}.", ""]

    rng = random.Random(SEED)
    h1, p1 = permutation(g["team"], g["solo"], tasks, rng)
    h3, p3 = permutation(g["team-full"], g["team"], tasks, rng)

    def h2stat(r):
        gt, gs = resample(g["team"], r), resample(g["solo"], r)
        return st.mean(st.mean(x["score"] for x in gt[t]) - k_estimate(gs[t], kt) for t in tasks)

    h2 = st.mean(st.mean(r["score"] for r in g["team"][t]) - K[t] for t in tasks)
    xs, lo2, hi2 = boot_ci(h2stat, random.Random(SEED))
    p2 = min(1.0, 2 * min(sum(x <= 0 for x in xs) / BOOTS, sum(x >= 0 for x in xs) / BOOTS))

    def ci(a, b):
        def s(r):
            ga, gb = resample(g[a], r), resample(g[b], r)
            return diff(ga, gb, tasks)
        _, lo, hi = boot_ci(s, random.Random(SEED))
        return lo, hi

    lo1, hi1 = ci("team", "solo")
    lo3, hi3 = ci("team-full", "team")
    adj = holm([p1, p2, p3])
    out += ["## Hypotheses", "", "| # | comparison | difference | 95% interval | p | Holm p |", "| --- | --- | --- | --- | --- | --- |",
            f"| H1 | team − solo (one-sided) | {fmt(h1)} | {fmt(lo1)} to {fmt(hi1)} | {fmt(p1, 4)} | {fmt(adj[0], 4)} |",
            f"| H2 | team − solo best-of-{kt} (two-sided) | {fmt(h2)} | {fmt(lo2)} to {fmt(hi2)} | {fmt(p2, 4)} | {fmt(adj[1], 4)} |",
            f"| H3 | team-full − team (one-sided) | {fmt(h3)} | {fmt(lo3)} to {fmt(hi3)} | {fmt(p3, 4)} | {fmt(adj[2], 4)} |", ""]
    hf = st.mean(st.mean(r["score"] for r in g["team-full"][t]) - KF[t] for t in tasks)
    out += [f"Secondary: team-full − solo best-of-{kf} = {fmt(hf)} (not tested).", ""]

    out += ["## Cost, time, verified passes", "", "| arm | runs | verified passes | mean cost | mean tokens | median minutes | cost per hidden test passed | timeouts |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        tests = sum(r["passed"] for r in rs)
        out.append(f"| {a} | {len(rs)} | {sum(r['verified'] for r in rs)} | ${st.mean(r['cost'] for r in rs):.3f} | "
                   f"{st.mean((r['tokens'] or {}).get('total_tokens', 0) for r in rs) / 1e6:.2f}M | {st.median(r['seconds'] for r in rs) / 60:.1f} | "
                   f"{'$%.4f' % (sum(r['cost'] for r in rs) / tests) if tests else 'n/a'} | {sum(r['status'] == 'timeout' for r in rs)} |")
    out.append("")

    out += ["## Did the team happen", "", "| arm | runs | with subagents | median subagents | planner edited files | spawns not fork_turns none | review rounds (median) | mvn install | paths outside the clone |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a and r["sessions"]]
        if not rs:
            continue
        s = [r["sessions"] for r in rs]
        out.append(f"| {a} | {len(rs)} | {sum(x['subagents'] > 0 for x in s)} | {st.median(x['subagents'] for x in s)} | "
                   f"{sum(x['planner_edits'] > 0 for x in s) if a != 'solo' else '—'} | "
                   f"{sum(any(sp.get('fork_turns') != 'none' for sp in x['spawns']) for x in s)} | "
                   f"{st.median(len(x['verdicts']) for x in s)} | {sum(x['mvn_install'] > 0 for x in s)} | {sum(bool(x['paths_outside_clone']) for x in s)} |")
    out.append("")

    out += ["## Reviews", "", "| arm | final review APPROVE | of those, hidden tests fail (rubber stamp) | any review CHANGES: mean score | first review APPROVE: mean score |",
            "| --- | --- | --- | --- | --- |"]
    for a in ("team", "team-full"):
        rs = [r for r in runs if r["arm"] == a and r["sessions"]]
        appr = [r for r in rs if r["sessions"]["final_verdict"] == "APPROVE"]
        stamp = [r for r in appr if r["passed"] < r["n"]]
        ch = [r["score"] for r in rs if "CHANGES" in r["sessions"]["verdicts"]]
        first = [r["score"] for r in rs if r["sessions"]["verdicts"][:1] == ["APPROVE"]]
        out.append(f"| {a} | {len(appr)} | {len(stamp)} | {fmt(st.mean(ch)) if ch else 'n/a'} | {fmt(st.mean(first)) if first else 'n/a'} |")
    out.append("")

    out += ["## False success claims", "", "Runs whose final report claimed success (the rig's claim check) while the independent check failed.", "",
            "| arm | false passes | runs with a claim |", "| --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        out.append(f"| {a} | {sum(r['claim_match'] == 'false_pass' for r in rs)} | {sum(r['claim_match'] is not None for r in rs)} |")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
