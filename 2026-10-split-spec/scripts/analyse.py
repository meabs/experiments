"""Analysis for split-spec, fixed before the measured runs (README, "Hypotheses and analysis").

Score per run: the share of the task's hidden tests passed (verify-summary.json "cases"; 0 if none ran); higher is
better. Arms are compared by the mean over tasks of each task's mean score.

- H1 split-part vs solo, H2 split-full vs split-part, H3 split-full vs team-spec: two-sided permutation tests, arm labels
  shuffled within each task (100,000 shuffles, seed 1); p = twice the smaller one-sided p, at most 1.
- Holm over H1 to H3 at alpha 0.05. Effect intervals: bootstrap within tasks, 10,000 resamples, seed 1.

Secondary: cost, tokens, wall time, cost per hidden test passed, verified passes; whether the split happened (coders,
coders overlapping in time, part files); whether coders kept to their brief (split-part coders reading TASK.md or
another part's file; split-full coders reading TASK.md); spec details carried into the part files and into the diffs;
files patched by more than one coder; the rubber stamp rate; false success claims.

Usage: python3 -I analyse.py <trial out dir> [<trial out dir> ...] > results/analysis.md
       (each dir holds runs/ and agent-homes/ from one trial file; sessions.json is written beside each run)
"""
import glob, os, random, re, statistics as st, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-swarm-tax", "scripts"))
import analyse as base  # noqa: E402  (swarm-tax's loader, permutation test and bootstrap, unchanged)
from analyse import SEED, boot_ci, by_task, diff, fmt, resample  # noqa: E402
from extra_checks import added, coverage  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-skills-impact", "scripts"))
from stats import holm  # noqa: E402

E = os.path.dirname(HERE)
base.E = E  # hidden test counts and task prompts come from this experiment's folders
base.HERE = HERE  # and sessions.json from this experiment's audit_run.py
ARMS = ["solo", "team-spec", "split-part", "split-full"]
HYP = [("H1", "split-part", "solo"), ("H2", "split-full", "split-part"), ("H3", "split-full", "team-spec")]


def spec(task):
    text = open(os.path.join(E, "tasks", task, "prompt.md")).read()
    return sorted(set(re.findall(r'"([a-zA-Z][a-zA-Z0-9]*)"\s*:', text))), sorted(set(re.findall(r"HTTP (\d{3})", text)))


def two_sided(ga, gb, tasks):
    obs, up = base.permutation(ga, gb, tasks, random.Random(SEED))
    _, down = base.permutation(gb, ga, tasks, random.Random(SEED))
    return obs, min(1.0, 2 * min(up, down))


def overlap(coders):
    """Pairs of coders whose working time overlapped (ISO timestamps), and coders in all."""
    iv = [(c["started"], c["ended"]) for c in coders if c.get("started") and c.get("ended")]
    return sum(1 for i in range(len(iv)) for j in range(i + 1, len(iv)) if iv[i][0] < iv[j][1] and iv[j][0] < iv[i][1])


def main(outs):
    runs, where = [], {}
    for out in outs:
        for r in base.load([out]):
            where[id(r)] = os.path.join(out, "runs", r["task"], r["arm"], "codex", str(r["rep"]))
            runs.append(r)
    for r in runs:
        rd = where[id(r)]
        r["spec"] = coverage(added(rd), *spec(r["task"]))
        parts = sorted(glob.glob(os.path.join(rd, "team-parts", "*.md")))
        r["parts"] = len(parts)
        r["part_spec"] = coverage("\n".join(open(p, errors="replace").read() for p in parts), *spec(r["task"])) if parts else None
    g = {a: by_task(runs, a) for a in ARMS}
    tasks = sorted(set.intersection(*(set(g[a]) for a in ARMS)))
    out = ["# split-spec: analysis", "", f"Runs: {len(runs)}; tasks with all four arms: {', '.join(tasks) or 'none'}.", "",
           "Scores are the share of each task's hidden tests passed, from 0 (none) to 1 (all); **higher is better**.", ""]
    if not tasks:
        print("\n".join(out + ["No task has runs in all four arms."]))
        return

    out += ["## Scores", "", "| task | " + " | ".join(ARMS) + " |", "| --- |" + " --- |" * len(ARMS)]
    for t in tasks:
        out.append(f"| {t} | " + " | ".join(fmt(st.mean(r["score"] for r in g[a][t])) for a in ARMS) + " |")
    out.append("| **mean over tasks** | " + " | ".join(fmt(st.mean(st.mean(r["score"] for r in g[a][t]) for t in tasks)) for a in ARMS) + " |")

    res = []
    for h, a, b in HYP:
        d, p = two_sided(g[a], g[b], tasks)
        _, lo, hi = boot_ci(lambda rr: diff(resample(g[a], rr), resample(g[b], rr), tasks), random.Random(SEED))
        res.append((h, a, b, d, lo, hi, p))
    adj = holm([x[-1] for x in res])
    out += ["", "## Hypotheses", "", "A difference is the first arm's score minus the second's (0.10 = 10 points of hidden tests passed); "
            "negative means the first arm did worse. Two-sided tests.", "",
            "| # | comparison | difference | 95% interval | p | Holm p |", "| --- | --- | --- | --- | --- | --- |"]
    for (h, a, b, d, lo, hi, p), q in zip(res, adj):
        out.append(f"| {h} | {a} − {b} | {fmt(d)} | {fmt(lo)} to {fmt(hi)} | {fmt(p, 4)} | {fmt(q, 4)} |")

    out += ["", "## Cost, time, verified passes", "", "Cost, tokens and time: lower is better.", "",
            "| arm | runs | verified passes | mean cost | mean tokens | median minutes | cost per hidden test passed | timeouts |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        tests = sum(r["passed"] for r in rs)
        out.append(f"| {a} | {len(rs)} | {sum(r['verified'] for r in rs)} | ${st.mean(r['cost'] for r in rs):.3f} | "
                   f"{st.mean((r['tokens'] or {}).get('total_tokens', 0) for r in rs) / 1e6:.2f}M | {st.median(r['seconds'] for r in rs) / 60:.1f} | "
                   f"{'$%.4f' % (sum(r['cost'] for r in rs) / tests) if tests else 'n/a'} | {sum(r['status'] == 'timeout' for r in rs)} |")

    out += ["", "## Did the split happen", "",
            "| arm | runs | median coders | runs with 2+ coders overlapping in time | median part files | planner edited source | spawns not fork_turns none | mvn install |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in ARMS[1:]:
        rs = [r for r in runs if r["arm"] == a and r["sessions"]]
        if not rs:
            continue
        s = [r["sessions"] for r in rs]
        out.append(f"| {a} | {len(rs)} | {st.median(len(x['coders']) for x in s)} | {sum(overlap(x['coders']) > 0 for x in s)} | "
                   f"{st.median(r['parts'] for r in rs)} | {sum(x['planner_code_edits'] > 0 for x in s)} | "
                   f"{sum(any(sp.get('fork_turns') != 'none' for sp in x['spawns']) for x in s)} | {sum(x['mvn_install'] > 0 for x in s)} |")

    out += ["", "## Did coders keep to their brief", "",
            "split-part coders were told to read only their own part file; split-full coders to read TASK.md and their part file; "
            "the team-spec coder to read TASK.md. From each coder's own commands (a command naming the file).", "",
            "| arm | coders | read TASK.md | read more than one part file | runs with a file patched by 2+ coders |", "| --- | --- | --- | --- | --- |"]
    for a in ARMS[1:]:
        rs = [r for r in runs if r["arm"] == a and r["sessions"]]
        cs = [c for r in rs for c in r["sessions"]["coders"]]
        other = sum(len(c["parts_read"]) > 1 for c in cs)
        shared = sum(1 for r in rs if any(v > 1 for v in Counter(f for c in r["sessions"]["coders"] for f in c["files_patched"]).values()))
        out.append(f"| {a} | {len(cs)} | {sum(c['read_task_md'] for c in cs)} | {other} | {shared} |")

    out += ["", "## Spec details carried through", "",
            "The share of the JSON field names and HTTP statuses each task's prompt states that appear in the planner's part files "
            "and in the change (higher means more of the stated interface carried through).", "",
            "| arm | in the part files | in the change |", "| --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        ps = [r["part_spec"] for r in rs if r["part_spec"] is not None]
        out.append(f"| {a} | {fmt(st.mean(ps), 2) if ps else '—'} | {fmt(st.mean(r['spec'] for r in rs), 2)} |")

    out += ["", "## Reviews and claims", "",
            "| arm | final review APPROVE | of those, hidden tests fail | false success claims (rig's claim check) | runs with a claim |",
            "| --- | --- | --- | --- | --- |"]
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        appr = [r for r in rs if (r["sessions"] or {}).get("final_verdict") == "APPROVE"]
        out.append(f"| {a} | {len(appr) if a != 'solo' else '—'} | {sum(not r['verified'] for r in appr) if a != 'solo' else '—'} | "
                   f"{sum(r['claim_match'] == 'false_pass' for r in rs)} | {sum(r['claim_match'] is not None for r in rs)} |")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
