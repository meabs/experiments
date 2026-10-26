"""Checks added after the measured runs (not pre-registered; see the README's amendment log). They describe, and test
nothing new.

1. Best-of-k with other pickers. The pre-registered picker (first run passing the visible check) kept every run, because
   every solo run compiled and passed its own tests. Two more pickers, each averaged over every k-subset of a task's six
   solo runs (ties shared equally):
   - own tests: the run whose diff adds the most @Test methods (a picker a user could apply without the hidden tests);
   - oracle: the run with the best hidden score. An upper bound only; no user has the hidden tests.
2. Spec details in the diffs: for each task, the JSON field names and HTTP statuses its prompt states, and the share of
   them that appear in a run's added lines (a field name as a word; a status as its number or its HttpStatus name).
   Indirect evidence on whether the team's coders had the spec: Codex stores the planner's messages encrypted.
3. Tasks won: per task, whether the team arm's mean is below, equal to or above solo's, with an exact sign test.

Usage: python3 -I extra_checks.py <trial out dir> ... > results/extra-checks.md
"""
import itertools, math, os, re, statistics as st, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import E, by_task, load  # noqa: E402

STATUS = {"200": "OK", "201": "CREATED", "204": "NO_CONTENT", "400": "BAD_REQUEST", "401": "UNAUTHORIZED",
          "403": "FORBIDDEN", "404": "NOT_FOUND", "409": "CONFLICT", "422": "UNPROCESSABLE_ENTITY"}


def added(rd):
    p = os.path.join(rd, "agent.diff")
    return "\n".join(l[1:] for l in open(p, errors="replace") if l.startswith("+") and not l.startswith("+++")) \
        if os.path.exists(p) else ""


def rd_of(out, r):
    return os.path.join(out, "runs", r["task"], r["arm"], "codex", str(r["rep"]))


def spec(task):
    text = open(os.path.join(E, "tasks", task, "prompt.md")).read()
    fields = sorted(set(re.findall(r'"([a-zA-Z][a-zA-Z0-9]*)"\s*:', text)))
    codes = sorted(set(re.findall(r"HTTP (\d{3})", text)))
    return fields, codes


def coverage(diff, fields, codes):
    hits = [bool(re.search(rf"\b{f}\b", diff)) for f in fields]
    hits += [bool(re.search(rf"\b{c}\b|\b{STATUS.get(c, c)}\b", diff)) for c in codes]
    return sum(hits) / len(hits) if hits else float("nan")


def pick_mean(runs, k, key):
    """Mean hidden score of the run chosen by key (highest wins, ties shared) over every k-subset."""
    tot, n = 0.0, 0
    for sub in itertools.combinations(runs, k):
        best = max(key(r) for r in sub)
        top = [r["score"] for r in sub if key(r) == best]
        tot += st.mean(top); n += 1
    return tot / n


def sign_p(lo, hi):
    n = lo + hi
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(lo, hi) + 1)) / 2 ** n) if n else 1.0


def main(outs):
    runs, where = [], {}
    for out in outs:
        rs = load([out])
        for r in rs:
            where[id(r)] = rd_of(out, r)
        runs += rs
    for r in runs:
        d = added(where[id(r)])
        r["tests_added"] = len(re.findall(r"@Test\b", d))
        r["spec"] = coverage(d, *spec(r["task"]))
    solo, team, full = by_task(runs, "solo"), by_task(runs, "team"), by_task(runs, "team-full")
    tasks = sorted(solo)

    print("# swarm-tax: checks added after the runs\n")
    print("Not pre-registered (README amendment log). Descriptive only.\n")
    print("## 1. Best-of-k with other pickers\n")
    print("| task | solo mean | visible check, k=2 | own tests, k=2 | oracle, k=2 | own tests, k=4 | oracle, k=4 | team | team-full |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    cols = defaultdict(list)
    for t in tasks:
        s = solo[t]
        row = {"solo": st.mean(r["score"] for r in s), "vis2": st.mean(r["score"] for r in s),
               "own2": pick_mean(s, 2, lambda r: r["tests_added"]), "or2": pick_mean(s, 2, lambda r: r["score"]),
               "own4": pick_mean(s, 4, lambda r: r["tests_added"]), "or4": pick_mean(s, 4, lambda r: r["score"]),
               "team": st.mean(r["score"] for r in team[t]), "full": st.mean(r["score"] for r in full[t])}
        for k, v in row.items():
            cols[k].append(v)
        print(f"| {t} | " + " | ".join(f"{v:.3f}" for v in row.values()) + " |")
    print("| **mean over tasks** | " + " | ".join(f"{st.mean(v):.3f}" for v in cols.values()) + " |\n")
    print("Every solo run passed the visible check, so that picker equals the solo mean. k=2 matches the team arm's "
          "spend and k=4 team-full's.\n")
    no_tests = sum(1 for r in runs if r["tests_added"] == 0)
    print(f"Runs whose diff adds no @Test method: {no_tests} of {len(runs)}, so the own-tests picker also ties every "
          "time and equals the solo mean. Nothing a user could see separates good solo runs from bad ones here; only "
          "the oracle does.\n")

    print("## 2. Spec details in the diffs\n")
    print("| task | fields + statuses in the prompt | solo | team | team-full |")
    print("| --- | --- | --- | --- | --- |")
    sc = defaultdict(list)
    for t in tasks:
        f, c = spec(t)
        vals = [st.mean(r["spec"] for r in g[t]) for g in (solo, team, full)]
        for a, v in zip(("solo", "team", "full"), vals):
            sc[a].append(v)
        print(f"| {t} | {len(f)} + {len(c)} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")
    print("| **mean over tasks** | | " + " | ".join(f"{st.mean(sc[a]):.2f}" for a in ("solo", "team", "full")) + " |\n")
    allr = [r for r in runs if not math.isnan(r["spec"])]
    print(f"Correlation of spec coverage with hidden score over all {len(allr)} runs: "
          f"{st.correlation([r['spec'] for r in allr], [r['score'] for r in allr]):.2f}.\n")

    print("## 3. Tasks won\n")
    print("| comparison | tasks lower | equal | higher | exact sign test, two-sided p |")
    print("| --- | --- | --- | --- | --- |")
    for name, g in (("team vs solo", team), ("team-full vs solo", full), ("team-full vs team", None)):
        lo = eq = hi = 0
        for t in tasks:
            a = st.mean(r["score"] for r in (g or full)[t])
            b = st.mean(r["score"] for r in (team if g is None else solo)[t])
            if abs(a - b) < 1e-9:
                eq += 1
            elif a < b:
                lo += 1
            else:
                hi += 1
        print(f"| {name} | {lo} | {eq} | {hi} | {sign_p(lo, hi):.3f} |")
    print("\nWith six tasks the smallest possible two-sided p is 0.031; this is a coarse check beside the within-task tests.")


if __name__ == "__main__":
    main(sys.argv[1:])
