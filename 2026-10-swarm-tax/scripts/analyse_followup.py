"""Analysis for the follow-up arm team-spec (README, "Follow-up: shared spec"), fixed before any follow-up run.

Score per run as in analyse.py. The solo and team runs are the main trial's; team-spec is run later the same way.
- H4 team-spec > team: one-sided permutation test, labels shuffled within each task (100,000 shuffles, seed 1).
- H5 team-spec vs solo: two-sided, the same permutation test (p = twice the smaller one-sided p, at most 1).
- Holm over H4 and H5 at alpha 0.05. Effect intervals: bootstrap within tasks, 10,000 resamples, seed 1.
Secondary: whether the coder and the reviewer read TASK.md (a command of theirs names it), spec details in the diffs
(as extra_checks.py), cost, the rubber stamp rate.

Usage: python3 -I analyse_followup.py <main solo dir> <main team dir> <team-spec dir> > results/followup-analysis.md
"""
import os, random, re, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse  # noqa: E402
from analyse import SEED, boot_ci, by_task, diff, fmt, load, resample  # noqa: E402
from extra_checks import added, coverage, spec  # noqa: E402

ARMS = ["solo", "team", "team-spec"]


def read_task_md(r):
    """(coder read TASK.md, reviewer read TASK.md): a command of theirs names it (sessions.json, from audit_run.py)."""
    return (r["sessions"] or {}).get("read_task_md") or {"coder": False, "reviewer": False}


def main(solo_dir, team_dir, spec_dir):
    runs = load([solo_dir]) + load([team_dir]) + load([spec_dir])
    where = {"solo": solo_dir, "team": team_dir, "team-spec": spec_dir}
    for r in runs:
        rd = os.path.join(where[r["arm"]], "runs", r["task"], r["arm"], "codex", str(r["rep"]))
        r["spec"] = coverage(added(rd), *spec(r["task"]))
    g = {a: by_task(runs, a) for a in ARMS}
    tasks = sorted(set(g["solo"]) & set(g["team"]) & set(g["team-spec"]))
    out = ["# swarm-tax follow-up: shared spec", "", f"Runs: {len(runs)}; tasks with all three arms: {', '.join(tasks)}.", "",
           "| task | solo | team | team-spec |", "| --- | --- | --- | --- |"]
    for t in tasks:
        out.append(f"| {t} | " + " | ".join(fmt(st.mean(r["score"] for r in g[a][t])) for a in ARMS) + " |")
    out.append("| **mean over tasks** | " + " | ".join(fmt(st.mean(st.mean(r["score"] for r in g[a][t]) for t in tasks)) for a in ARMS) + " |")

    h4, p4 = analyse.permutation(g["team-spec"], g["team"], tasks, random.Random(SEED))
    h5, up = analyse.permutation(g["team-spec"], g["solo"], tasks, random.Random(SEED))
    _, down = analyse.permutation(g["solo"], g["team-spec"], tasks, random.Random(SEED))
    p5 = min(1.0, 2 * min(up, down))

    def ci(a, b):
        _, lo, hi = boot_ci(lambda rr: diff(resample(g[a], rr), resample(g[b], rr), tasks), random.Random(SEED))
        return lo, hi

    (l4, u4), (l5, u5) = ci("team-spec", "team"), ci("team-spec", "solo")
    adj = analyse.holm([p4, p5])
    out += ["", "## Hypotheses", "", "| # | comparison | difference | 95% interval | p | Holm p |", "| --- | --- | --- | --- | --- | --- |",
            f"| H4 | team-spec − team (one-sided) | {fmt(h4)} | {fmt(l4)} to {fmt(u4)} | {fmt(p4, 4)} | {fmt(adj[0], 4)} |",
            f"| H5 | team-spec − solo (two-sided) | {fmt(h5)} | {fmt(l5)} to {fmt(u5)} | {fmt(p5, 4)} | {fmt(adj[1], 4)} |", ""]

    out += ["## Secondary", "", "| arm | runs | mean cost | spec details in diff | final APPROVE | of those, hidden tests fail | coder read TASK.md | reviewer read TASK.md |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        appr = [r for r in rs if (r["sessions"] or {}).get("final_verdict") == "APPROVE"]
        reads = [read_task_md(r) for r in rs] if a == "team-spec" else None
        out.append(f"| {a} | {len(rs)} | ${st.mean(r['cost'] for r in rs):.3f} | {st.mean(r['spec'] for r in rs):.2f} | "
                   f"{len(appr) if a != 'solo' else '—'} | {sum(not r['verified'] for r in appr) if a != 'solo' else '—'} | "
                   f"{sum(x['coder'] for x in reads) if reads else '—'} | {sum(x['reviewer'] for x in reads) if reads else '—'} |")
    print("\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:4])
