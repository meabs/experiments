"""Analysis for test-skill, fixed before the measured runs (README, "Hypotheses and analysis").

COPIED from 2026-10-test-skill/scripts/analyse.py at e3908706 for 2026-10-test-skill-local, with three changes, marked
"LOCAL CHANGE": (1) arm G (`stop`) added to the arm lists; (2) tokens taken from session.json when run.json has none
(a run that timed out); (3) the tasks folder is the original experiment's. Nothing else differs.

The unit is the task. Primary measure: a relevant test (relevance.json, from scripts/relevance.sh): the agent's own tests
all pass with its change, and at least one fails, or does not compile, on the original code. For each task and arm, the
count is 0 to 3. H1 (skill vs instruction), H2 (skill-revised vs skill) and H3 (gate vs instruction) use the per-task
difference in counts: an exact one-sided sign-flip permutation test over tasks, Holm-adjusted together at alpha 0.05.
Effects are the mean per-task difference in rate with a bootstrap interval over tasks (10,000 resamples, seed 1).

Secondary, reported and labelled so: relevant tests, instruction vs none; verified pass rate of every arm vs none and
gate vs instruction (two-sided, unadjusted); medium vs the guided arm with the most verified passes (pass rate and cost
per verified pass); cost per verified pass and per relevant test; process measures; the gate's records; false success
claims. Exploratory: pass rate of runs with and without a relevant test, in each arm.

Usage: python3 -I analyse.py <runs dir> [<runs dir> ...] > results/analysis.md   (trial, trial-medium, trial-gate)
"""
import glob, gzip, itertools, json, os, random, re, statistics as st, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(E, "..", "2026-10-skills-impact", "scripts"))
from stats import holm  # noqa: E402

RUNS = sys.argv[1:]
ORDER = ["none", "instruction", "skill", "skill-revised", "medium", "gate", "stop"]  # LOCAL CHANGE (1)
LABEL = {"none": "A none", "instruction": "B instruction", "skill": "C skill", "skill-revised": "D revised skill",
         "medium": "E medium effort", "gate": "F gate", "stop": "G stop"}  # LOCAL CHANGE (1)
GUIDED = ["instruction", "skill", "skill-revised", "gate"]
BOOT_APP = re.compile(r"spring-boot:run|java\s+-jar|curl\s[^\n]*localhost|wget\s[^\n]*localhost|http://localhost:\d+")
GATE_FILES = re.compile(r"\.codex/(gate|hooks\.json)")


def cost(t):
    return ((t["input"] - t["cache_read"]) * 0.20 + t["cache_read"] * 0.02 + t["output"] * 1.20) / 1e6


def kind(t):
    return "N" if os.path.exists(os.path.join(E, "..", "2026-10-test-skill", "tasks", t, "naive.patch")) else "R"  # LOCAL CHANGE (3)


def commands(text):
    out = []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        it = e.get("item") or {}
        if e.get("type") == "item.completed" and it.get("type") == "command_execution":
            out.append(it.get("command", ""))
    return out


def load(runs):
    out = []
    for f in sorted(glob.glob(os.path.join(runs, "*/*/codex/*/run.json"))):
        rd = os.path.dirname(f)
        task, arm = rd.split(os.sep)[-4:-2]
        d = json.load(open(f))
        if d.get("tokens") is None:  # LOCAL CHANGE (2): timed-out run; use the Codex session's last token totals
            sj = os.path.join(rd, "session.json")
            u = (json.load(open(sj)).get("tokens") or {}) if os.path.exists(sj) else {}
            d["tokens"] = {"input": u.get("input_tokens", 0), "cache_read": u.get("cached_input_tokens", 0),
                           "output": u.get("output_tokens", 0), "cache_write": 0, "total": u.get("total_tokens", 0)}
        sp = os.path.join(rd, "verify-summary.json")
        s = json.load(open(sp)) if os.path.exists(sp) else {"pass": False}
        rp = os.path.join(rd, "relevance.json")
        rel = json.load(open(rp)) if os.path.exists(rp) else None
        raw = os.path.join(rd, "raw.out")
        text = (open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")).read()
        cmds = commands(text)
        tests = set()
        for c in cmds:
            for m in re.findall(r"-Dtest=([\w,#*$.]+)", c):
                tests |= {x.split("#")[0] for x in m.split(",")}
        full = any(re.search(r"\bmvn\b[^|;&]*\stest\b", c) and "-Dtest" not in c for c in cmds)
        gates = []
        for g in sorted(glob.glob(os.path.join(rd, "gate-*.json")), key=lambda p: int(re.findall(r"gate-(\d+)\.json", p)[0])):
            gates.append(json.load(open(g)))
        claim = d.get("claim") if isinstance(d.get("claim"), dict) else {}
        out.append(dict(
            task=task, arm=arm, status=d["status"], passed=bool(s.get("pass")) and d["status"] == "ok",
            graded=s.get("hidden_tests") == s.get("hidden_expected"), keeps_broken=bool(s.get("keeps_broken")),
            tokens=d["tokens"]["total"], cost=cost(d["tokens"]), seconds=d["seconds"],
            relevance=rel, relevant=bool(rel and rel.get("relevant")),
            reason=(rel or {}).get("reason", "no relevance record").split(":")[0],
            orig_compile=bool(rel and rel.get("relevant") and rel.get("original_compile_error")),
            wrote_test=bool(rel and rel.get("classes")),
            ran_tests=bool(tests) or full, only_smoke=tests == {"ActuatorTest"} and not full,
            read_skill="verify-api/SKILL.md" in " ".join(cmds),
            boot_app=any(BOOT_APP.search(c) for c in cmds),
            touched_gate=any(GATE_FILES.search(c) for c in cmds),
            gates=gates, overclaim=claim.get("result") == "passed" and not s.get("pass")))
    return out


rows = [r for d in RUNS for r in load(d)]
ARMS = [a for a in ORDER if any(r["arm"] == a for r in rows)]
tasks = sorted({r["task"] for r in rows})
cell = defaultdict(list)
for r in rows:
    cell[(r["task"], r["arm"])].append(r)
reps = max(len(v) for v in cell.values())


def count(t, a, key):
    return sum(r[key] for r in cell[(t, a)])


def signflip_p(diffs, two_sided=False):
    obs = sum(diffs)
    nz = [d for d in diffs if d]
    hits = total = 0
    for signs in itertools.product((1, -1), repeat=len(nz)):
        s = sum(x * y for x, y in zip(nz, signs))
        total += 1
        hits += (abs(s) >= abs(obs)) if two_sided else (s >= obs)
    return hits / total if total else 1.0


def boot(values, n=10000):
    rng = random.Random(1)
    means = sorted(st.mean([rng.choice(values) for _ in values]) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def compare(a, b, key, two_sided=False):
    d = [count(t, a, key) - count(t, b, key) for t in tasks]
    rate = [x / reps for x in d]
    return d, st.mean(rate), boot(rate), signflip_p(d, two_sided)


def bsw(d):
    return f"{sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)}"


def total(a, key):
    return f"{sum(count(t, a, key) for t in tasks)}/{reps * len(tasks)}"


print(f"# test-skill: analysis\n\n{len(rows)} runs over {len(tasks)} tasks, arms {', '.join(ARMS)}; statuses: "
      f"{dict(Counter(r['status'] for r in rows))}; fully graded: {sum(r['graded'] for r in rows)}; "
      f"with a relevance record: {sum(r['relevance'] is not None for r in rows)}.\n")
for key, title in [("relevant", "Relevant tests per task (primary)"), ("passed", "Verified passes per task")]:
    print(f"## {title} (of {reps})\n")
    print("| task | kind | " + " | ".join(LABEL[a] for a in ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
    for t in tasks:
        print(f"| {t} | {kind(t)} | " + " | ".join(str(count(t, a, key)) for a in ARMS) + " |")
    print("| **total** | | " + " | ".join(f"**{total(a, key)}**" for a in ARMS) + " |\n")

print("## Hypotheses (preregistered): relevant tests\n")
print("| # | comparison | tasks better / same / worse | mean per-task difference in rate (95% CI) | p (one-sided) | Holm p |")
print("| --- | --- | --- | --- | --- | --- |")
hyp = [("H1", "skill", "instruction"), ("H2", "skill-revised", "skill"), ("H3", "gate", "instruction")]
hyp = [h for h in hyp if h[1] in ARMS and h[2] in ARMS]
res = {h: compare(a, b, "relevant") for h, a, b in hyp}
adj = dict(zip([h for h, _, _ in hyp], holm([res[h][3] for h, _, _ in hyp]))) if hyp else {}
for h, a, b in hyp:
    d, m, (lo, hi), p = res[h]
    print(f"| {h} | {a} vs {b} | {bsw(d)} | {m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | {p:.3f} | {adj[h]:.3f} |")

print("\n## Secondary (two-sided, unadjusted)\n")
print("| measure | comparison | tasks better / same / worse | difference (95% CI) | p |\n| --- | --- | --- | --- | --- |")
sec = [("relevant", "instruction", "none")] + [("passed", a, "none") for a in ARMS if a != "none"]
if "gate" in ARMS and "instruction" in ARMS:
    sec.append(("passed", "gate", "instruction"))
best = max([a for a in GUIDED if a in ARMS], key=lambda a: sum(count(t, a, "passed") for t in tasks), default=None)
if "medium" in ARMS and best:
    sec.append(("passed", "medium", best))
for key, a, b in sec:
    if a in ARMS and b in ARMS:
        d, m, (lo, hi), p = compare(a, b, key, True)
        print(f"| {key} | {a} vs {b} | {bsw(d)} | {m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | {p:.3f} |")
if best:
    print(f"\nThe guided arm with the most verified passes, compared with medium above: {best}.")


def cost_per(ts, a, key):
    n = sum(count(t, a, key) for t in ts)
    return sum(r["cost"] for t in ts for r in cell[(t, a)]) / n if n else float("inf")


print("\n## Cost, time and process (secondary)\n")
cols = ["runs", "verified passes", "relevant tests", "relevant only because the original did not compile", "wrote a test",
        "ran tests", "ran only ActuatorTest", "read verify-api", "tried to start the app", "mean tokens", "total $",
        "$ per verified pass", "$ per relevant test", "median s", "neighbour breaks", "false success claims (of failed)"]
print("| arm | " + " | ".join(cols) + " |\n| --- |" + " --- |" * len(cols))
for a in ARMS:
    rs = [r for r in rows if r["arm"] == a]
    failed = [r for r in rs if not r["passed"]]
    n = lambda k: sum(r[k] for r in rs)  # noqa: E731
    print(f"| {LABEL[a]} | {len(rs)} | {n('passed')} | {n('relevant')} | {n('orig_compile')} | {n('wrote_test')} | "
          f"{n('ran_tests')} | {n('only_smoke')} | {n('read_skill')} | {n('boot_app')} | "
          f"{st.mean(r['tokens'] for r in rs) / 1e6:.2f}M | {sum(r['cost'] for r in rs):.2f} | "
          f"{cost_per(tasks, a, 'passed'):.3f} | {cost_per(tasks, a, 'relevant'):.3f} | {st.median(r['seconds'] for r in rs):.0f} | "
          f"{n('keeps_broken')} | {sum(r['overclaim'] for r in failed)}/{len(failed)} |")
print("\nWhy runs had no relevant test:\n")
print("| arm | " + " | ".join(sorted({r['reason'] for r in rows if not r['relevant']})) + " |")
reasons = sorted({r['reason'] for r in rows if not r['relevant']})
print("| --- |" + " --- |" * len(reasons))
for a in ARMS:
    c = Counter(r["reason"] for r in rows if r["arm"] == a and not r["relevant"])
    print(f"| {LABEL[a]} | " + " | ".join(str(c[x]) for x in reasons) + " |")

if "gate" in ARMS:
    g = [r for r in rows if r["arm"] == "gate"]
    blocked = [r for r in g if r["gates"] and r["gates"][0].get("blocked")]
    print("\n## The gate (arm F)\n")
    print(f"- Runs with a gate record: {sum(bool(r['gates']) for r in g)}/{len(g)}; checks per run: "
          f"{dict(Counter(len(r['gates']) for r in g))}.")
    print(f"- Blocked at the first attempt to finish: {len(blocked)}; why: "
          f"{dict(Counter(r['gates'][0].get('reason', '').split(':')[0] for r in blocked))}.")
    second = [r for r in blocked if len(r["gates"]) > 1]
    print(f"- Of those, the second check found a relevant test in {sum(bool(r['gates'][1].get('relevant')) for r in second)}"
          f"/{len(second)}; verified passes among blocked runs: {sum(r['passed'] for r in blocked)}/{len(blocked)}.")
    print(f"- Passed the gate (last check relevant) but failed the hidden tests: "
          f"{sum(bool(r['gates']) and bool(r['gates'][-1].get('relevant')) and not r['passed'] for r in g)}.")
    gs = [x.get("gate_seconds", 0) for r in g for x in r["gates"]]
    if gs:
        print(f"- Gate check time: median {st.median(gs):.0f} s, max {max(gs)} s.")
    print(f"- Runs whose commands touched the gate's files: {sum(r['touched_gate'] for r in g)}.")
    print(f"- Gate's last verdict vs the grader's relevance check, agreeing: "
          f"{sum(bool(r['gates']) and bool(r['gates'][-1].get('relevant')) == r['relevant'] for r in g)}/{sum(bool(r['gates']) for r in g)}.")

print("\n## Exploratory\n")
for a in ARMS:
    rs = [r for r in rows if r["arm"] == a]
    yes, no = [r for r in rs if r["relevant"]], [r for r in rs if not r["relevant"]]
    print(f"- {a}: runs with a relevant test passed {sum(r['passed'] for r in yes)}/{len(yes)}; without, "
          f"{sum(r['passed'] for r in no)}/{len(no)} (not causal).")
print(f"\nTotal estimated spend (list prices): ${sum(r['cost'] for r in rows):.2f}.")
