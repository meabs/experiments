"""Analysis, as fixed in the design: per arm and level, left-out requirements met (Wilson 95%), ticket pass rate,
developer's cost, coverage, agent's cost; the four confirmatory comparisons (stratified permutation test, Holm).

  python3 -I analyse.py            prints the tables (markdown) and writes results/summary.json
"""
import glob, json, math, os, random, re, statistics as st

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.environ.get("GRILL_WORK", os.path.expanduser("~/code/benchmark/grilling-work"))
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}  # gpt-5.6-luna list prices, $ per million tokens
LEVEL = {"C1": "Clear", "C2": "Clear", "S1": "Some", "S2": "Some", "L1": "Lots", "L2": "Lots"}
# Left-out requirements by kind (brief labels). L2 rd is "guessable" (amendment): in the main score, not in H3.
HEAD = {"S1": ["b"], "S2": ["b"], "L1": ["c", "d"], "L2": ["c"]}
REPO = {"S1": ["a"], "S2": ["a"], "L1": ["a", "b"], "L2": ["a", "b"]}
GUESS = {"L2": ["d"]}
ARMS = ["T", "Q", "G", "GD", "GY"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


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
    q = set(re.findall(r"\*\*Q(\d+)", s))
    return len(q) if q else s.count("❓")


def load():
    key = json.load(open(os.path.join(W, "key.json")))
    rows = []
    for d in sorted(glob.glob(os.path.join(W, "*"))):
        name = os.path.basename(d)
        if not os.path.exists(os.path.join(d, "grade.json")):
            continue
        if not (name.startswith("main-") or name.startswith("s2-") or name in key):
            continue
        m = json.load(open(os.path.join(d, "meta.json")))
        g = json.load(open(os.path.join(d, "grade.json")))
        arm, rep = (key[name]["arm"], key[name]["rep"]) if name in key else (m["arm"], int(name.rsplit("-", 1)[1]))
        t = sorted(glob.glob(os.path.join(d, "turns", "[0-9][0-9].agent.md")))
        agent = [open(f).read() for f in t]
        devs = [open(f).read() for f in sorted(glob.glob(os.path.join(d, "turns", "[0-9][0-9].dev.md")))][1:]
        labels = []
        for f in sorted(glob.glob(os.path.join(d, "turns", "[0-9][0-9].labels.json"))):
            labels += json.load(open(f))
        touched = {l["item"][1] for l in labels if l.get("item")}
        tok, cost = tokens(d)
        reqs = g["reqs"] if g["ticket_pass"] else {k: False for k in g["reqs"]}
        # Built in the same turn as asking: the first message has questions and the code changed in that turn.
        asked_first = bool(agent) and questions(agent[0]) > 0
        first_diff = asked_first and m["turns"] >= 1 and len(devs) == 0
        rows.append({
            "run": name, "task": m["task"], "stage": m["stage"], "arm": arm, "rep": rep,
            "ticket_pass": g["ticket_pass"], "reqs": reqs, "met": sum(reqs.values()), "possible": g["possible"],
            "rounds": len(devs), "questions": sum(questions(a) for a in agent),
            "words_read": sum(words(a) for a in agent[:-1]) if devs else 0,
            "words_typed": sum(words(x) for x in devs),
            "corrections": sum(1 for l in labels if l["rule"] == "correct"),
            "point_repo": sum(1 for l in labels if l["rule"] == "point to repo"),
            "your_call": sum(1 for l in labels if l["rule"] == "your call"),
            "cap": sum(1 for l in labels if l["rule"] == "cap"),
            "touched": sorted(touched), "asked": asked_first, "built_without_answers": first_diff,
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


def head_met(r):
    return sum(r["reqs"].get(k, False) for k in HEAD.get(r["task"], []))


def main():
    rows = load()
    s1 = [r for r in rows if r["stage"] == 1]
    s2 = [r for r in rows if r["stage"] == 2]
    out = {"rows": rows}

    print("## Left-out requirements met, stage 1 (higher is better)\n")
    print("| Arm | Clear: ticket passed | Some: met / possible (95% CI) | Lots: met / possible (95% CI) | All S+L: met / possible | Ticket passed, all tasks |")
    print("| --- | --- | --- | --- | --- | --- |")
    for a in ARMS:
        cells = []
        rs = [r for r in s1 if r["arm"] == a]
        c = [r for r in rs if LEVEL[r["task"]] == "Clear"]
        cells.append(f"{sum(r['ticket_pass'] for r in c)} of {len(c)}")
        for lev in ["Some", "Lots"]:
            x = [r for r in rs if LEVEL[r["task"]] == lev]
            k, n = sum(r["met"] for r in x), sum(r["possible"] for r in x)
            p, lo, hi = wilson(k, n)
            cells.append(f"{k} / {n} ({lo:.0%}–{hi:.0%})")
        x = [r for r in rs if LEVEL[r["task"]] != "Clear"]
        cells.append(f"{sum(r['met'] for r in x)} / {sum(r['possible'] for r in x)}")
        cells.append(f"{sum(r['ticket_pass'] for r in rs)} of {len(rs)}")
        print(f"| {a} | " + " | ".join(cells) + " |")

    print("\n## By kind of requirement, Some and Lots tasks (higher is better)\n")
    print("| Arm | In the repo: met / possible | In my head: met / possible (95% CI) | Guessable (L2 rd) |")
    print("| --- | --- | --- | --- |")
    for a in ARMS:
        rs = [r for r in s1 if r["arm"] == a and LEVEL[r["task"]] != "Clear"]
        rk = sum(sum(r["reqs"].get(k, False) for k in REPO[r["task"]]) for r in rs)
        rn = sum(len(REPO[r["task"]]) for r in rs)
        hk = sum(head_met(r) for r in rs)
        hn = sum(len(HEAD[r["task"]]) for r in rs)
        p, lo, hi = wilson(hk, hn)
        gk = sum(r["reqs"].get("d", False) for r in rs if r["task"] == "L2")
        print(f"| {a} | {rk} / {rn} | {hk} / {hn} ({lo:.0%}–{hi:.0%}) | {gk} of 3 |")

    print("\n## Per requirement, stage 1: runs that met it, of 3 (higher is better)\n")
    items = [(t, k) for t in ["S1", "S2", "L1", "L2"] for k in sorted(REPO[t] + HEAD[t] + GUESS.get(t, []))]
    print("| Requirement | Kind | " + " | ".join(ARMS) + " |")
    print("| --- | --- | " + " | ".join("---" for _ in ARMS) + " |")
    for t, k in items:
        kind = "repo" if k in REPO[t] else "head" if k in HEAD[t] else "guessable"
        cells = [str(sum(r["reqs"].get(k, False) for r in s1 if r["arm"] == a and r["task"] == t)) for a in ARMS]
        print(f"| {t} r{k} | {kind} | " + " | ".join(cells) + " |")

    print("\n## Developer's cost and dialogue, stage 1 interview arms (per run, mean; lower cost is better)\n")
    print("| Arm | Level | Runs that asked first | Built without waiting for answers | Rounds answered | Questions asked | Words the developer read | Words the developer typed | Corrections from the brief | Point-to-repo | Stalls |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for a in ["Q", "G", "GD", "GY"]:
        for lev in ["Clear", "Some", "Lots"]:
            x = [r for r in s1 if r["arm"] == a and LEVEL[r["task"]] == lev]
            mean = lambda f: st.mean(f(r) for r in x)
            print(f"| {a} | {lev} | {sum(r['asked'] for r in x)} of {len(x)} | {sum(r['built_without_answers'] for r in x)} | "
                  f"{mean(lambda r: r['rounds']):.1f} | {mean(lambda r: r['questions']):.1f} | {mean(lambda r: r['words_read']):.0f} | "
                  f"{mean(lambda r: r['words_typed']):.0f} | {mean(lambda r: r['corrections']):.1f} | {sum(r['point_repo'] for r in x)} | {sum(r['stalls'] for r in x)} |")

    print("\n## Coverage of \"in my head\" requirements: did the dialogue touch it? (Q, G, GD)\n")
    print("| Requirement | " + " | ".join(["Q touched / met", "G touched / met", "GD touched / met"]) + " |")
    print("| --- | --- | --- | --- |")
    for t in ["S1", "S2", "L1", "L2"]:
        for k in HEAD[t] + GUESS.get(t, []):
            cells = []
            for a in ["Q", "G", "GD"]:
                x = [r for r in s1 if r["arm"] == a and r["task"] == t]
                cells.append(f"{sum(k in r['touched'] for r in x)} / {sum(r['reqs'].get(k, False) for r in x)}")
            print(f"| {t} r{k} | " + " | ".join(cells) + " |")

    print("\n## Agent's cost, stage 1 (per run, mean; lower is better)\n")
    print("| Arm | Level | Wall time, min | Tokens in (k) | Tokens out (k) | Cost, $ list price |")
    print("| --- | --- | --- | --- | --- | --- |")
    for a in ARMS:
        for lev in ["Clear", "Some", "Lots"]:
            x = [r for r in s1 if r["arm"] == a and LEVEL[r["task"]] == lev]
            print(f"| {a} | {lev} | {st.mean(r['seconds'] for r in x) / 60:.1f} | {st.mean(r['tokens']['input'] for r in x) / 1e3:.0f} | "
                  f"{st.mean(r['tokens']['output'] for r in x) / 1e3:.1f} | {st.mean(r['cost'] for r in x):.3f} |")

    if s2:
        print("\n## Stage 2: follow-up ticket, no developer (higher is better)\n")
        print("| Task | Docs: ticket passed | Docs: met / possible | No docs: ticket passed | No docs: met / possible | Carried-over rule met, docs / no docs |")
        print("| --- | --- | --- | --- | --- | --- |")
        for t in ["S1", "S2", "L1", "L2"]:
            d = [r for r in s2 if r["task"] == t and r["arm"] == "D"]
            n = [r for r in s2 if r["task"] == t and r["arm"] == "N"]
            print(f"| {t}F | {sum(r['ticket_pass'] for r in d)} of {len(d)} | {sum(r['met'] for r in d)} / {sum(r['possible'] for r in d)} | "
                  f"{sum(r['ticket_pass'] for r in n)} of {len(n)} | {sum(r['met'] for r in n)} / {sum(r['possible'] for r in n)} | "
                  f"{sum(r['reqs'].get('a', False) for r in d)} / {sum(r['reqs'].get('a', False) for r in n)} |")

    lots = [r for r in s1 if LEVEL[r["task"]] == "Lots"]
    sl = [r for r in s1 if LEVEL[r["task"]] != "Clear"]
    tests = [("H1: G − T, Lots, requirements met per run", perm(lots, "G", "T", lambda r: r["met"])),
             ("H3a: G − GY, in-my-head requirements met per run", perm(sl, "G", "GY", head_met)),
             ("H3b: GY − T, in-my-head requirements met per run", perm(sl, "GY", "T", head_met))]
    if s2:
        tests.append(("H5: docs − no docs, stage 2 requirements met per run", perm(s2, "D", "N", lambda r: r["met"])))
    adj = holm([p for _, (_, p) in tests])
    print("\n## Confirmatory comparisons (stratified permutation test, 10,000 permutations, seed 1; Holm-adjusted)\n")
    print("| Comparison | Difference in mean per run | p | Holm p |")
    print("| --- | --- | --- | --- |")
    for (name, (d, p)), q in zip(tests, adj):
        print(f"| {name} | {d:+.2f} | {p:.4f} | {q:.4f} |")
    out["tests"] = [{"name": nm, "diff": d, "p": p, "holm": q} for (nm, (d, p)), q in zip(tests, adj)]
    total = sum(r["cost"] for r in rows)
    print(f"\nTotal agent spend at list prices: ${total:.2f}.")
    os.makedirs(os.path.join(E, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(E, "results", "summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
