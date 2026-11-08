"""ASF-1 analysis, as pre-registered in README.md sections 5 and 7.

Reads arm A from results/main/A/runs/<T>/A/codex/<rep>/ (trialrig) and arms B and C from results/main/bc-runs.jsonl
and results/main/runs/<T>/<ARM>/codex/<rep>/. Writes results/main/analysis.json and results/main/runs.csv.

- Score: share of the ticket's hidden tests passed; 0 if the change doesn't compile or there is no PR (B, C).
- An arm's score: mean over tickets of the ticket's mean score. H1-H3 use the six hard tickets.
- H1 C>A and H2 C>B: one-sided permutation within ticket; H3 B vs A: two-sided. 100,000 shuffles, seed 1.
  Holm across H1-H3. Bootstrap 95% intervals within ticket, 10,000 resamples, seed 1.
- Cost ratios C/A and B/A with bootstrap intervals (reported, not tested). Easy tickets described.
- Sensitivity (disclosed, not pre-registered; README log item 13): H1-H3 again without runs lost to an expired
  GitHub token.
"""
import csv
import glob
import json
import os
import random
import sys

X = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(X, "results", "main")
SESS = os.path.expanduser("~/code/benchmark/asf-runtime/home/.codex/sessions")
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}  # gpt-5.6-luna, $ per million tokens
HARD = ["CATEGORYDELETE", "CUSTOMERCART", "PRODUCTDELETE", "REVIEWS", "STOCK", "SUPPORTORDERS"]
EASY = ["RETURNS", "VISIBILITY"]
ARMS = ["A", "B", "C"]
HYP = [("H1", "C", "A", "greater"), ("H2", "C", "B", "greater"), ("H3", "B", "A", "two-sided")]


def cost(inp, cached, out):
    return ((inp - cached) * PRICE["input"] + cached * PRICE["cached"] + out * PRICE["output"]) / 1e6


def token_expired(job):
    """True if any of the job's Codex sessions saw GitHub reject its token."""
    for f in glob.glob(os.path.join(SESS, "**", "rollout-*.jsonl"), recursive=True):
        with open(f) as fh:
            head = fh.readline()
            if job not in head:
                continue
            if "Invalid username or token" in head + fh.read():
                return True
    return False


def load():
    rows = []
    for d in sorted(glob.glob(os.path.join(MAIN, "A", "runs", "*", "A", "codex", "*"))):
        ticket, rep = d.split(os.sep)[-4], int(d.split(os.sep)[-1])
        v = json.load(open(os.path.join(d, "verify-summary.json")))
        r = json.load(open(os.path.join(d, "run.json")))
        t = r.get("tokens", {})
        n = v.get("hidden_expected") or v["hidden_tests"]
        passed = sum(c == "pass" for c in v.get("cases", {}).values())
        compiles = v["mvn_exit"] == 0
        rows.append(dict(ticket=ticket, arm="A", rep=rep, hidden=n, passed=passed if compiles else 0, compiles=compiles,
                         delivered=True, score=passed / n if compiles else 0.0, state=r.get("status"), stages=1,
                         approvals=0, seconds=r.get("seconds"), input=t.get("input", 0), cached=t.get("cache_read", 0),
                         output=t.get("output", 0), cost=cost(t.get("input", 0), t.get("cache_read", 0), t.get("output", 0)),
                         luna_only=True, leaks=0, token_expired=False, reviewer_approved=None, reviews=0))
    for b in map(json.loads, open(os.path.join(MAIN, "bc-runs.jsonl"))):
        d = os.path.join(MAIN, "runs", b["ticket"], b["arm"], "codex", str(b["rep"]))
        n = b["hidden_total"]
        if n is None:  # no PR: the ticket's hidden test count from arm A's run of it
            n = next(r["hidden"] for r in rows if r["ticket"] == b["ticket"])
        delivered, compiles = bool(b["pr"]), bool(b["compiles"])
        job = json.load(open(os.path.join(d, "machinist-job.json")))
        verdicts = [((r.get("report") or "") + (r.get("summary") or "")) for r in job.get("runs", []) if r.get("command") == "review"]
        approved = ((job.get("workflow") or {}).get("factory") or {}).get("verdict") == "approved"
        t = b["tokens"]
        rows.append(dict(ticket=b["ticket"], arm=b["arm"], rep=b["rep"], hidden=n,
                         passed=b["hidden_passed"] if compiles else 0, compiles=compiles, delivered=delivered,
                         score=b["hidden_passed"] / n if (delivered and compiles) else 0.0, state=b["state"],
                         stages=len(b["stages"]), approvals=len(b["approvals"]), seconds=b["wall_s"],
                         input=t["input"], cached=t["cached"], output=t["output"], cost=b["cost_usd"],
                         luna_only=b["luna_only"], leaks=b["leaks"], token_expired=token_expired(b["job"]),
                         reviewer_approved=approved if b["arm"] == "C" else None, reviews=len(verdicts)))
    return rows


def by_ticket(rows, tickets, key="score"):
    return {(t, a): [r[key] for r in rows if r["ticket"] == t and r["arm"] == a] for t in tickets for a in ARMS}


def arm_mean(by, arm, tickets):
    return sum(sum(by[(t, arm)]) / len(by[(t, arm)]) for t in tickets) / len(tickets)


def permutation(by, tickets, a, b, alternative, n=100_000, seed=1):
    rng = random.Random(seed)
    obs = arm_mean(by, a, tickets) - arm_mean(by, b, tickets)
    pools = {t: by[(t, a)] + by[(t, b)] for t in tickets}
    sizes = {t: len(by[(t, a)]) for t in tickets}
    hits = 0
    for _ in range(n):
        diff = 0.0
        for t in tickets:
            p = pools[t][:]
            rng.shuffle(p)
            k = sizes[t]
            diff += sum(p[:k]) / k - sum(p[k:]) / (len(p) - k)
        diff /= len(tickets)
        if (diff >= obs - 1e-12) if alternative == "greater" else (abs(diff) >= abs(obs) - 1e-12):
            hits += 1
    return obs, (hits + 1) / (n + 1)


def bootstrap(by, tickets, a, b, ratio=False, n=10_000, seed=1):
    rng = random.Random(seed)
    ds = []
    for _ in range(n):
        ma = mb = 0.0
        for t in tickets:
            xa = [rng.choice(by[(t, a)]) for _ in by[(t, a)]]
            xb = [rng.choice(by[(t, b)]) for _ in by[(t, b)]]
            ma += sum(xa) / len(xa)
            mb += sum(xb) / len(xb)
        ds.append(ma / mb if ratio else (ma - mb) / len(tickets))
    ds.sort()
    return ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def tests_for(rows):
    by = by_ticket(rows, HARD)
    tests = []
    for h, a, b, alt in HYP:
        obs, p = permutation(by, HARD, a, b, alt)
        tests.append(dict(hypothesis=h, a=a, b=b, alternative=alt, diff=obs, p=p, ci=list(bootstrap(by, HARD, a, b))))
    for t, adj in zip(tests, holm([t["p"] for t in tests])):
        t["p_holm"] = adj
    return tests


def main():
    rows = load()
    counts = {a: sum(r["arm"] == a for r in rows) for a in ARMS}
    excluded = [r for r in rows if not r["luna_only"] or r["leaks"]]
    rows = [r for r in rows if r["luna_only"] and not r["leaks"]]
    tests = tests_for(rows)
    expired = [r for r in rows if r["token_expired"]]
    sensitivity = tests_for([r for r in rows if not r["token_expired"]]) if expired else None
    cby = by_ticket(rows, HARD + EASY, "cost")
    per_arm = {}
    for a in ARMS:
        rs = [r for r in rows if r["arm"] == a]
        hard = [r for r in rs if r["ticket"] in HARD]
        states = {}
        for r in rs:
            states[r["state"]] = states.get(r["state"], 0) + 1
        per_arm[a] = dict(
            runs=len(rs), hard_score=arm_mean(by_ticket(rows, HARD), a, HARD),
            easy_score=arm_mean(by_ticket(rows, EASY), a, EASY),
            fully_correct=sum(r["score"] == 1 for r in rs), fully_correct_hard=sum(r["score"] == 1 for r in hard),
            no_pr=sum(not r["delivered"] for r in rs), not_compiling=sum(r["delivered"] and not r["compiles"] for r in rs),
            cost_total=sum(r["cost"] for r in rs), cost_per_run=sum(r["cost"] for r in rs) / len(rs),
            cost_per_run_hard=sum(r["cost"] for r in hard) / len(hard),
            seconds_mean=sum(r["seconds"] or 0 for r in rs) / len(rs),
            tokens_per_run={k: sum(r[k] for r in rs) / len(rs) for k in ("input", "cached", "output")},
            states=states, approvals=sum(r["approvals"] for r in rs), token_expired=sum(r["token_expired"] for r in rs),
            stages_mean=sum(r["stages"] for r in rs) / len(rs),
            reviewer_approved=sum(bool(r["reviewer_approved"]) for r in rs) if a == "C" else None)
    ratios = {f"{a}/A": dict(ratio=sum(cby[(t, a)][i] for t in HARD + EASY for i in range(len(cby[(t, a)]))) /
                             sum(cby[(t, "A")][i] for t in HARD + EASY for i in range(len(cby[(t, "A")]))),
                             ci=list(bootstrap(cby, HARD + EASY, a, "A", ratio=True))) for a in ("B", "C")}
    per_ticket = {t: {a: dict(mean=sum(v) / len(v), scores=v) for a in ARMS for v in [by_ticket(rows, [t])[(t, a)]]}
                  for t in HARD + EASY}
    out = dict(counts=counts, excluded=[(r["ticket"], r["arm"], r["rep"]) for r in excluded], tests=tests,
               sensitivity_without_token_expiry=dict(runs=[(r["ticket"], r["arm"], r["rep"]) for r in expired],
                                                     tests=sensitivity),
               cost_ratios=ratios, per_arm=per_arm, per_ticket=per_ticket, price=PRICE)
    json.dump(out, open(os.path.join(MAIN, "analysis.json"), "w"), indent=1)
    with open(os.path.join(MAIN, "runs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({k: out[k] for k in ("counts", "excluded", "tests", "sensitivity_without_token_expiry", "cost_ratios")}, indent=1))
    for a in ARMS:
        p = per_arm[a]
        print(a, f"hard {p['hard_score']:.3f} easy {p['easy_score']:.3f} full {p['fully_correct']} "
                 f"${p['cost_per_run']:.3f}/run {p['seconds_mean']:.0f}s states {p['states']}")
    for t in HARD + EASY:
        print(f"{t:15s}", " ".join(f"{a}={per_ticket[t][a]['mean']:.2f}" for a in ARMS))


if __name__ == "__main__":
    sys.exit(main())
