"""Analysis, as fixed in the design: in-my-head rules met per rule and per level, all left-out requirements, coverage
(did the dialogue touch the rule?), developer's and agent's cost; hypothesis 1 (non-inferiority of S against G on flat
tickets, two-stage bootstrap over rules) and hypotheses 2, 3, 4a, 4b (stratified permutation tests, Holm).

  python3 -I analyse.py            prints the tables (markdown) and writes results/summary.json
"""
import glob, json, os, random, re, statistics as st

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.environ.get("GVP_WORK", os.path.expanduser("~/code/benchmark/gvp-work"))
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}  # gpt-5.6-luna list prices, $ per million tokens
TASKS = ["S1", "S2", "L1", "L2", "M1", "N1", "N2"]
LEVEL = {"S1": "Few, flat", "S2": "Few, flat", "L1": "Few, flat", "L2": "Few, flat", "M1": "Many, flat",
         "N1": "Nested", "N2": "Nested"}
LEVELS = ["Few, flat", "Many, flat", "Nested"]
# Left-out requirements by kind (brief labels). L2 rd is "guessable" (from GRL): in the totals, not one of the 15.
HEAD = {"S1": ["b"], "S2": ["b"], "L1": ["c", "d"], "L2": ["c"], "M1": ["c", "d", "e", "f"], "N1": ["b", "c", "d"],
        "N2": ["c", "d", "e"]}
REPO = {"S1": ["a"], "S2": ["a"], "L1": ["a", "b"], "L2": ["a", "b"], "M1": ["a", "b"], "N1": ["a"], "N2": ["a", "b"]}
GUESS = {"L2": ["d"]}
RULE_NAMES = {
    ("S1", "b"): "support may only add internal notes", ("S2", "b"): "resolution saved as a customer-visible comment",
    ("L1", "c"): "support can freeze, only admins unfreeze", ("L1", "d"): "audit note on freeze and unfreeze",
    ("L2", "c"): "new assignee must be assigned to the account", ("M1", "c"): "support can only lower the limit",
    ("M1", "d"): "£5,000 ceiling", ("M1", "e"): "savings accounts fixed", ("M1", "f"): "audit note with old and new limit",
    ("N1", "b"): "over £100 waits for approval (parent)", ("N1", "c"): "how approval works (child)",
    ("N1", "d"): "can't approve your own (child)", ("N2", "c"): "money must be moved first (parent)",
    ("N2", "d"): "where the money can go (child)", ("N2", "e"): "the move is booked on both accounts (child)"}
ARMS = ["T", "G", "S", "K"]
DEV = ["G", "S", "K"]
FLAT = ["S1", "S2", "L1", "L2", "M1"]
MARGIN = -0.15


def tokens(d):
    """Sums every thread's final token count (the main agent and any subagents) from the run's Codex sessions."""
    tot = {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
    for f in glob.glob(os.path.join(d, "codex-home", "sessions", "**", "*.jsonl"), recursive=True):
        last = None
        for line in open(f):
            if '"token_count"' in line:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                info = (e.get("payload") or {}).get("info")
                if info and info.get("total_token_usage"):
                    last = info["total_token_usage"]
        if last:
            tot["input"] += last.get("input_tokens", 0)
            tot["cached"] += last.get("cached_input_tokens", 0)
            tot["output"] += last.get("output_tokens", 0)
            tot["reasoning"] += last.get("reasoning_output_tokens", 0)
    cost = ((tot["input"] - tot["cached"]) * PRICE["input"] + tot["cached"] * PRICE["cached"]
            + tot["output"] * PRICE["output"]) / 1e6
    return tot, cost


def words(s):
    return len(re.findall(r"\S+", s))


def questions(s):
    """Questions in one agent message: grilling's **Qn** or ❓ markers, else numbered items at line start."""
    q = set(re.findall(r"\*\*Q(\d+)", s))
    if q:
        return len(q)
    if "❓" in s:
        return s.count("❓")
    return len(set(re.findall(r"(?m)^\s*(\d+)\.\s", s)))


def load():
    key = json.load(open(os.path.join(W, "key.json")))
    rows = []
    for d in sorted(glob.glob(os.path.join(W, "*"))):
        name = os.path.basename(d)
        if not os.path.exists(os.path.join(d, "grade.json")):
            continue
        if not (name.startswith("main-") or name in key):
            continue
        m = json.load(open(os.path.join(d, "meta.json")))
        g = json.load(open(os.path.join(d, "grade.json")))
        arm, rep = (key[name]["arm"], key[name]["rep"]) if name in key else (m["arm"], int(name.rsplit("-", 1)[1]))
        agent = [open(f).read() for f in sorted(glob.glob(os.path.join(d, "turns", "[0-9][0-9].agent.md")))]
        devs = [open(f).read() for f in sorted(glob.glob(os.path.join(d, "turns", "[0-9][0-9].dev.md")))][1:]
        labels = []
        for f in sorted(glob.glob(os.path.join(d, "turns", "[0-9][0-9].labels.json"))):
            labels += json.load(open(f))
        touched = sorted({l["item"][1] for l in labels if l.get("item")})
        corrected = sorted({l["item"][1] for l in labels if l.get("item") and l["rule"] == "correct"})
        tok, cost = tokens(d)
        reqs = g["reqs"] if g["ticket_pass"] else {k: False for k in g["reqs"]}
        asked = agent[: len(devs)]  # the messages the developer answered
        rows.append({
            "run": name, "task": m["task"], "arm": arm, "rep": rep, "ticket_pass": g["ticket_pass"], "reqs": reqs,
            "met": sum(reqs.values()), "possible": g["possible"],
            "head_met": sum(reqs.get(k, False) for k in HEAD[m["task"]]), "head_possible": len(HEAD[m["task"]]),
            "rounds": len(devs), "questions": sum(questions(a) for a in asked),
            "words_read": sum(words(a) for a in asked), "words_typed": sum(words(x) for x in devs),
            "corrections": sum(1 for l in labels if l["rule"] == "correct"),
            "point_repo": sum(1 for l in labels if l["rule"] == "point to repo"),
            "your_call": sum(1 for l in labels if l["rule"] == "your call"),
            "cap": sum(1 for l in labels if l["rule"] == "cap"),
            "touched": touched, "corrected": corrected, "never_waited": arm != "T" and len(devs) == 0,
            "stalls": sum(1 for x in m.get("turn_log", []) if x.get("stalled")),
            "seconds": sum(x["seconds"] for x in m.get("turn_log", [])), "tokens": tok, "cost": cost,
        })
    return rows


def perm(rows, a, b, f, seed=1, n=10000):
    """Stratified (by task) permutation test of mean(f) for arm a minus arm b; two-sided."""
    strata = {}
    for r in rows:
        if r["arm"] in (a, b):
            strata.setdefault(r["task"], []).append((r["arm"], f(r)))
    obs = st.mean([v for s in strata.values() for x, v in s if x == a]) - \
        st.mean([v for s in strata.values() for x, v in s if x == b])
    rng, hits = random.Random(seed), 0
    for _ in range(n):
        A, B = [], []
        for s in strata.values():
            labs = [x for x, _ in s]
            rng.shuffle(labs)
            for lab, (_, v) in zip(labs, s):
                (A if lab == a else B).append(v)
        if abs(st.mean(A) - st.mean(B)) >= abs(obs) - 1e-12:
            hits += 1
    return obs, (hits + 1) / (n + 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0] * len(ps), 0
    for k, i in enumerate(order):
        run = max(run, min(1, (len(ps) - k) * ps[i]))
        adj[i] = run
    return adj


def noninferiority(rows, a, b, tasks, seed=1, n=10000):
    """Hypothesis 1: mean over rules of (proportion of a's runs meeting the rule − b's), with a one-sided 95% lower
    bound from a two-stage bootstrap: resample rules, then runs within each rule and arm."""
    rules = [(t, k) for t in tasks for k in HEAD[t]]
    runs = {(t, k, arm): [int(r["reqs"].get(k, False)) for r in rows if r["task"] == t and r["arm"] == arm]
            for t, k in rules for arm in (a, b)}
    diff = lambda rs, pick: st.mean(st.mean(pick(runs[(t, k, a)])) - st.mean(pick(runs[(t, k, b)])) for t, k in rs)
    obs = diff(rules, lambda x: x)
    rng, boots = random.Random(seed), []
    for _ in range(n):
        rs = [rng.choice(rules) for _ in rules]
        boots.append(diff(rs, lambda x: [rng.choice(x) for _ in x]))
    boots.sort()
    return obs, boots[int(0.05 * n)]


def main():
    rows = load()
    out = {"rows": rows}
    by = lambda **kw: [r for r in rows if all(r[k] == v for k, v in kw.items())]

    print("## In-my-head rules met, by level (rule checks: rules × 5 runs; higher is better)\n")
    print("| Level | Rules | " + " | ".join(ARMS) + " |")
    print("| --- | --- | " + " | ".join("---" for _ in ARMS) + " |")
    for lev in LEVELS:
        ts = [t for t in TASKS if LEVEL[t] == lev]
        nr = sum(len(HEAD[t]) for t in ts)
        cells = []
        for a in ARMS:
            x = [r for r in rows if r["arm"] == a and r["task"] in ts]
            cells.append(f"{sum(r['head_met'] for r in x)} / {sum(r['head_possible'] for r in x)}")
        print(f"| {lev} | {nr} | " + " | ".join(cells) + " |")
    cells = [f"{sum(r['head_met'] for r in by(arm=a))} / {sum(r['head_possible'] for r in by(arm=a))}" for a in ARMS]
    print("| **All** | 15 | " + " | ".join(cells) + " |")

    print("\n## Per rule: runs that met it, of 5 (higher is better)\n")
    print("| Task | Rule | Kind | " + " | ".join(ARMS) + " |")
    print("| --- | --- | --- | " + " | ".join("---" for _ in ARMS) + " |")
    for t in TASKS:
        for k in sorted(REPO[t] + HEAD[t] + GUESS.get(t, [])):
            kind = "repo" if k in REPO[t] else "head" if k in HEAD[t] else "guessable"
            cells = [str(sum(r["reqs"].get(k, False) for r in by(arm=a, task=t))) for a in ARMS]
            print(f"| {t} | r{k} {RULE_NAMES.get((t, k), '')} | {kind} | " + " | ".join(cells) + " |")

    print("\n## All left-out requirements and ticket pass (higher is better)\n")
    print("| Arm | All left-out: met / possible | Ticket passed |")
    print("| --- | --- | --- |")
    for a in ARMS:
        x = by(arm=a)
        print(f"| {a} | {sum(r['met'] for r in x)} / {sum(r['possible'] for r in x)} | {sum(r['ticket_pass'] for r in x)} of {len(x)} |")

    print("\n## Why a rule was missed (in-my-head rules, interview arms)\n")
    print("| Arm | Rule checks | Met | Missed: never raised | Missed: raised but built wrong | Wrong recommendations corrected |")
    print("| --- | --- | --- | --- | --- | --- |")
    for a in DEV:
        met = never = wrong = n = 0
        for r in by(arm=a):
            for k in HEAD[r["task"]]:
                n += 1
                if r["reqs"].get(k, False):
                    met += 1
                elif k in r["touched"]:
                    wrong += 1
                else:
                    never += 1
        corr = sum(len([k for k in r["corrected"] if k in HEAD[r["task"]]]) for r in by(arm=a))
        print(f"| {a} | {n} | {met} | {never} | {wrong} | {corr} |")

    print("\n## Coverage per in-my-head rule: runs whose dialogue touched it / runs that met it (of 5)\n")
    print("| Task | Rule | " + " | ".join(f"{a} touched / met" for a in DEV) + " |")
    print("| --- | --- | " + " | ".join("---" for _ in DEV) + " |")
    for t in TASKS:
        for k in HEAD[t]:
            cells = [f"{sum(k in r['touched'] for r in by(arm=a, task=t))} / {sum(r['reqs'].get(k, False) for r in by(arm=a, task=t))}"
                     for a in DEV]
            print(f"| {t} | r{k} {RULE_NAMES[(t, k)]} | " + " | ".join(cells) + " |")

    print("\n## Developer's cost and dialogue (per run, mean; lower cost is better)\n")
    print("| Arm | Level | Never waited for an answer | Rounds answered | Questions asked | Words the developer read | Words the developer typed | Corrections | Point-to-repo | Stalls |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for a in DEV:
        for lev in LEVELS:
            x = [r for r in by(arm=a) if LEVEL[r["task"]] == lev]
            mean = lambda f: st.mean(f(r) for r in x)
            print(f"| {a} | {lev} | {sum(r['never_waited'] for r in x)} of {len(x)} | {mean(lambda r: r['rounds']):.1f} | "
                  f"{mean(lambda r: r['questions']):.1f} | {mean(lambda r: r['words_read']):.0f} | {mean(lambda r: r['words_typed']):.0f} | "
                  f"{mean(lambda r: r['corrections']):.1f} | {sum(r['point_repo'] for r in x)} | {sum(r['stalls'] for r in x)} |")

    print("\n## Agent's cost (per run, mean; lower is better)\n")
    print("| Arm | Level | Wall time, min | Tokens in (k) | Tokens out (k) | Cost, $ list price |")
    print("| --- | --- | --- | --- | --- | --- |")
    for a in ARMS:
        for lev in LEVELS:
            x = [r for r in by(arm=a) if LEVEL[r["task"]] == lev]
            print(f"| {a} | {lev} | {st.mean(r['seconds'] for r in x) / 60:.1f} | {st.mean(r['tokens']['input'] for r in x) / 1e3:.0f} | "
                  f"{st.mean(r['tokens']['output'] for r in x) / 1e3:.1f} | {st.mean(r['cost'] for r in x):.3f} |")

    d1, lo1 = noninferiority(rows, "S", "G", FLAT)
    print("\n## Hypothesis 1: S against G on flat tickets (non-inferiority, margin −0.15)\n")
    print("| Difference S − G, mean over 9 rules of the proportion of runs meeting the rule | One-sided 95% lower bound | Non-inferior? |")
    print("| --- | --- | --- |")
    print(f"| {d1:+.3f} | {lo1:+.3f} | {'yes' if lo1 > MARGIN else 'no'} |")
    out["h1"] = {"diff": d1, "lower": lo1, "margin": MARGIN, "noninferior": lo1 > MARGIN}

    nested = [r for r in rows if LEVEL[r["task"]] == "Nested"]
    many = [r for r in rows if r["task"] in ("M1", "N1", "N2")]
    tests = [("H2: G − S, nested tickets, in-my-head rules met per run", perm(nested, "G", "S", lambda r: r["head_met"])),
             ("H3: G − K, M1 + nested tickets, in-my-head rules met per run", perm(many, "G", "K", lambda r: r["head_met"])),
             ("H4a: S − G, words the developer read per run", perm(rows, "S", "G", lambda r: r["words_read"])),
             ("H4b: K − G, words the developer read per run", perm(rows, "K", "G", lambda r: r["words_read"]))]
    adj = holm([p for _, (_, p) in tests])
    print("\n## Hypotheses 2–4 (stratified permutation test, 10,000 permutations, seed 1; Holm-adjusted)\n")
    print("| Comparison | Difference in mean per run | p | Holm p |")
    print("| --- | --- | --- | --- |")
    for (name, (d, p)), q in zip(tests, adj):
        print(f"| {name} | {d:+.2f} | {p:.4f} | {q:.4f} |")
    out["tests"] = [{"name": nm, "diff": d, "p": p, "holm": q} for (nm, (d, p)), q in zip(tests, adj)]

    # Description, not tests: S against G on each level, and K against S.
    print("\n## Description: in-my-head rules met per run, mean (higher is better)\n")
    print("| Level | " + " | ".join(ARMS) + " |")
    print("| --- | " + " | ".join("---" for _ in ARMS) + " |")
    for lev in LEVELS:
        print(f"| {lev} | " + " | ".join(f"{st.mean(r['head_met'] for r in by(arm=a) if LEVEL[r['task']] == lev):.2f}" for a in ARMS) + " |")
    total = sum(r["cost"] for r in rows)
    print(f"\nTotal agent spend at list prices: ${total:.2f}.")
    os.makedirs(os.path.join(E, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(E, "results", "summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
