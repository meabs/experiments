"""Analysis for repo-skills, fixed before the measured runs (README, "Hypotheses and analysis").

The unit is the task; for each task and arm, passes is 0 to 3. H1 compares repo-skills with none through the per-task
difference in passes: an exact one-sided sign-flip permutation test over tasks, at alpha 0.05. The effect is the mean
per-task difference in pass rate with a bootstrap interval over tasks (10,000 resamples, seed 1).

Secondary, reported and labelled so: cost per verified pass (pooled; ratio repo-skills / none with tasks resampled),
neighbour breaks on the neighbour-break tasks, false success claims, and the process measures (Maven test runs,
API-level tests written, the app started or called). Exploratory: pass rate of repo-skills runs that did and did not
write or run an API-level check; results by kind of task.

Usage: python3 -I analyse.py <runs dir> > results/analysis.md
"""
import glob, gzip, itertools, json, os, random, re, statistics as st, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(E, "..", "2026-10-skills-impact", "scripts"))
import process  # noqa: E402  (test-file-first and TDD evidence, unchanged from skills-impact)

RUNS = sys.argv[1]
ARMS = ["none", "repo-skills"]
LABEL = {"none": "A none", "repo-skills": "B repo skills"}


def kind(t):
    return "N" if os.path.exists(os.path.join(E, "tasks", t, "naive.patch")) else "R"


def cost(t):
    return ((t["input"] - t["cache_read"]) * 0.20 + t["cache_read"] * 0.02 + t["output"] * 1.20) / 1e6


SKILL = re.compile(r"\.agents/skills/[^ ]*SKILL\.md")
BOOT_APP = re.compile(r"spring-boot:run|java\s+-jar|curl\s[^\n]*localhost|wget\s[^\n]*localhost|http://localhost:\d+")


def commands(text):
    """The shell commands the agent ran (command_execution items in the Codex event stream)."""
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
        sp = os.path.join(rd, "verify-summary.json")
        s = json.load(open(sp)) if os.path.exists(sp) else {"pass": False}
        raw = os.path.join(rd, "raw.out")
        text = (open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")).read()
        ev = process.events_codex(iter(text.splitlines(True)))
        ns = [l.split("\t") for l in open(os.path.join(rd, "agent.numstat")).read().splitlines() if l.strip()]
        own = {os.path.basename(p)[:-5] for _, _, p in ns if "/src/test/" in p and p.endswith(".java")}
        diff = open(os.path.join(rd, "agent.diff"), errors="replace").read()
        claim = d.get("claim") if isinstance(d.get("claim"), dict) else {}
        out.append(dict(task=task, arm=arm, status=d["status"], passed=bool(s.get("pass")) and d["status"] == "ok",
                        keeps_broken=bool(s.get("keeps_broken")), tokens=d["tokens"]["total"], cost=cost(d["tokens"]),
                        seconds=d["seconds"], tff=process.test_file_first(ev), tdd=process.classify_tdd(ev, own)[0],
                        test_runs=sum(e["k"] == "test" for e in ev),
                        test_lines=sum(int(a) + int(b) for a, b, p in ns if a != "-" and "/src/test/" in p),
                        api_test=bool(re.search(r"^\+.*(TestRestTemplate|ServicesTestSupport|MockMvc)", diff, re.M | re.I)),
                        boot_app=any(BOOT_APP.search(c) for c in commands(text)),
                        skill=any(SKILL.search(c) for c in commands(text)),
                        overclaim=claim.get("result") == "passed" and not s.get("pass")))
    return out



def detail(rd):
    raw = os.path.join(rd, "raw.out")
    text = (open(raw) if os.path.exists(raw) else gzip.open(raw + ".gz", "rt")).read()
    cmds, msg = [], ""
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        it = e.get("item") or {}
        if e.get("type") == "item.completed" and it.get("type") == "command_execution":
            cmds.append(it)
        if e.get("type") == "item.completed" and it.get("type") == "agent_message":
            msg = it.get("text", "")
    caveat = False
    m = list(re.finditer(r"VERIFICATION:\s*(\{.*\})", msg))
    if m:
        try:
            v = json.loads(m[-1].group(1)).get("could_not_verify")
            v = " ".join(map(str, v)) if isinstance(v, list) else str(v or "")
            caveat = v.strip().lower().rstrip(".") not in ("", "none", "n/a", "nothing")
        except ValueError:
            pass
    start = any(re.search(r"spring-boot:run|java\s+-jar", c.get("command", "")) for c in cmds)
    up = any(re.search(r"Started ShopApplication|Tomcat started", c.get("aggregated_output") or "") for c in cmds)
    curl = any(re.search(r"(curl|wget)\s[^\n]*localhost", c.get("command", "")) and c.get("exit_code") == 0 for c in cmds)
    return start, up, curl, caveat



rows = load(RUNS)
tasks = sorted({r["task"] for r in rows})
cell = defaultdict(list)
for r in rows:
    cell[(r["task"], r["arm"])].append(r)


def passes(t, a):
    return sum(r["passed"] for r in cell[(t, a)])


def broken(t, a):
    return sum(r["keeps_broken"] for r in cell[(t, a)])


def signflip_p(diffs, two_sided=False):
    obs = sum(diffs)
    nz = [d for d in diffs if d]
    count = total = 0
    for signs in itertools.product((1, -1), repeat=len(nz)):
        s = sum(x * y for x, y in zip(nz, signs))
        total += 1
        count += (abs(s) >= abs(obs)) if two_sided else (s >= obs)
    return count / total if total else 1.0


def boot(values, stat=st.mean, n=10000):
    rng = random.Random(1)
    means = sorted(stat([rng.choice(values) for _ in values]) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


reps = max(len(v) for v in cell.values())
print(f"# repo-skills: analysis\n\n{len(rows)} runs over {len(tasks)} tasks; statuses: "
      f"{ {s: sum(r['status'] == s for r in rows) for s in sorted({r['status'] for r in rows})} }.\n")
print(f"## Passes per task (of {reps})\n")
print("| task | kind | " + " | ".join(LABEL[a] for a in ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
for t in tasks:
    print(f"| {t} | {kind(t)} | " + " | ".join(str(passes(t, a)) for a in ARMS) + " |")
print("| **total** | | " + " | ".join(f"**{sum(passes(t, a) for t in tasks)}/{reps * len(tasks)}**" for a in ARMS) + " |")

print("\n## H1 (preregistered)\n")
d = [passes(t, "repo-skills") - passes(t, "none") for t in tasks]
rate = [x / reps for x in d]
lo, hi = boot(rate)
print("| hypothesis | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p (one-sided) |\n| --- | --- | --- | --- |")
print(f"| repo-skills beats none | {sum(x > 0 for x in d)} / {sum(x == 0 for x in d)} / {sum(x < 0 for x in d)} | "
      f"{st.mean(rate) * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f}) | {signflip_p(d):.3f} |")


def cost_per_pass(ts, a):
    n = sum(passes(t, a) for t in ts)
    return sum(r["cost"] for t in ts for r in cell[(t, a)]) / n if n else float("inf")


ratio = cost_per_pass(tasks, "repo-skills") / cost_per_pass(tasks, "none")
rng = random.Random(1)
bs = []
for _ in range(10000):
    s = [rng.choice(tasks) for _ in tasks]
    v, c = cost_per_pass(s, "repo-skills"), cost_per_pass(s, "none")
    if v != float("inf") and c != float("inf"):
        bs.append(v / c)
bs.sort()
print(f"\n**Secondary: cost per verified pass**, repo-skills over none = {ratio:.2f} "
      f"(95% CI {bs[int(0.025 * len(bs))]:.2f} to {bs[int(0.975 * len(bs)) - 1]:.2f}, resampling tasks).\n")
nt = [t for t in tasks if kind(t) == "N"]
print(f"**Secondary: neighbour breaks** ({len(nt)} neighbour-break tasks): runs with a failing keeps... test, none "
      f"{sum(broken(t, 'none') for t in nt)}, repo-skills {sum(broken(t, 'repo-skills') for t in nt)}.\n")

print("## Cost, time and process (secondary)\n")
det = {a: {} for a in ARMS}
for f in sorted(glob.glob(os.path.join(RUNS, "*/*/codex/*/run.json"))):
    rd = os.path.dirname(f)
    task, arm, _, rep = rd.split(os.sep)[-4:]
    det[arm][(task, rep)] = detail(rd)
print("| arm | runs | verified passes | mean tokens | total $ | $ per verified pass | median s | ran Maven tests | "
      "wrote tests | API-level test written | tried to start the app | called the app | read a skill | "
      "neighbour breaks | false success claims (of failed) |")
print("| --- |" + " --- |" * 14)
for a in ARMS:
    rs = [r for r in rows if r["arm"] == a]
    n = sum(r["passed"] for r in rs)
    failed = [r for r in rs if not r["passed"]]
    dd = list(det[a].values())
    print(f"| {LABEL[a]} | {len(rs)} | {n} | {st.mean(r['tokens'] for r in rs) / 1e6:.2f}M | {sum(r['cost'] for r in rs):.2f} | "
          f"{sum(r['cost'] for r in rs) / n if n else float('nan'):.3f} | {st.median(r['seconds'] for r in rs):.0f} | "
          f"{sum(r['test_runs'] > 0 for r in rs)} | {sum(r['test_lines'] > 0 for r in rs)} | {sum(r['api_test'] for r in rs)} | "
          f"{sum(x[0] for x in dd)} | {sum(x[2] for x in dd)} | {sum(r['skill'] for r in rs)} | "
          f"{sum(r['keeps_broken'] for r in rs)} | {sum(r['overclaim'] for r in failed)}/{len(failed)} |")

print("\n## Exploratory\n")
b = [r for r in rows if r["arm"] == "repo-skills"]
for name, f in [("wrote an API-level test", lambda r: r["api_test"]), ("ran Maven tests", lambda r: r["test_runs"] > 0)]:
    yes = [r for r in b if f(r)]
    no = [r for r in b if not f(r)]
    print(f"- repo-skills runs that {name}: {sum(r['passed'] for r in yes)}/{len(yes)} passed; "
          f"that did not: {sum(r['passed'] for r in no)}/{len(no)} (not causal: harder tasks may draw more checking).")
print("\n| kind | tasks | " + " | ".join(LABEL[a] for a in ARMS) + " |\n| --- | --- |" + " --- |" * len(ARMS))
for k in ["N", "R"]:
    ts = [t for t in tasks if kind(t) == k]
    if ts:
        print(f"| {k} | {len(ts)} | " + " | ".join(f"{sum(passes(t, a) for t in ts)}/{reps * len(ts)}" for a in ARMS) + " |")
print(f"\nTotal estimated spend (list prices): ${sum(r['cost'] for r in rows):.2f}.")
