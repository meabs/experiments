"""Analysis for okf-local, fixed before the measured runs (README, "Hypotheses and analysis").

A run passes if it finished (status ok) and its hidden test passed (verified). Arms are compared by the mean over the
four tasks of each task's pass rate (or mean wall time), so every task counts equally.

- H1 okf > no_okf, H2 okf > source (passes); H3 okf < source (wall time). One-sided permutation tests, arm labels
  shuffled within each task, 100,000 shuffles, seed 1. Effect intervals: bootstrap within tasks, 10,000, seed 1.
  Holm over H1 to H3 at alpha 0.05.
- Secondary (no tests): source vs no_okf, timeouts, correct-but-timed-out, tokens, turns, energy, use of the arm,
  and the hosted test G results side by side.

Usage: python3 -I analyse.py <out dir> > results/analysis.md   (out dir holds <arm>/runs/... and power.csv)
"""
import glob, json, os, random, statistics as st, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-skills-impact", "scripts"))
from stats import holm  # noqa: E402

ARMS = ["no_okf", "okf", "source"]
TASKS = ["g1_delete_item", "g2_add_voucher", "g3_checkout_request", "g4_orders_list"]
PERMS, BOOTS, SEED = 100_000, 10_000, 1
# OKF test G (gpt-5.6-luna), passes of 5 per task, from results/G-harder-crossrepo-change-tasks.md at 5a09027
HOSTED = {"no_okf": [3, 0, 0, 0], "source": [5, 4, 4, 5], "okf": [5, 5, 3, 5]}
PRICE_KWH = 0.25


def load_power(out):
    p = os.path.join(out, "power.csv")
    if not os.path.exists(p):
        return []
    rows = []
    for line in open(p).read().splitlines()[1:]:
        try:
            t, w = line.split(",")
            rows.append((float(t), float(w)))
        except ValueError:
            pass
    return rows


def energy_wh(power, start, seconds):
    if not power or start is None:
        return None
    w = [v for t, v in power if start <= t <= start + seconds]
    return sum(w) / 3600 if w else None  # one sample a second


def load(out):
    power = load_power(out)
    runs = []
    for f in glob.glob(os.path.join(out, "*", "runs", "*", "*", "codex", "*", "run.json")):
        r = json.load(open(f))
        if r["arm"] not in ARMS:
            continue
        try:
            start = datetime.fromisoformat(r["started"]).timestamp()
        except (TypeError, ValueError):
            start = None
        raw = open(os.path.join(os.path.dirname(f), "raw.out"), errors="replace").read()
        runs.append({
            "task": r["question"], "arm": r["arm"], "rep": r["rep"], "status": r["status"],
            "pass": 1 if r["status"] == "ok" and r.get("verified") else 0,
            "timeout_correct": 1 if r["status"] == "timeout" and r.get("verified") else 0,
            "seconds": r["seconds"], "tokens": (r.get("tokens") or {}).get("total"), "turns": r.get("turns"),
            "used": bool(r.get("used_tool")), "wh": energy_wh(power, start, r["seconds"]),
            "left_workspace": "code/experiments" in raw or (r["arm"] != "source" and "okf-local/pr2" in raw),
        })
    return runs


def by_task(runs, arm, key):
    return {t: [r[key] for r in runs if r["arm"] == arm and r["task"] == t] for t in TASKS}


def stat(a, b):
    ts = [t for t in TASKS if a[t] and b[t]]
    return st.mean(st.mean(a[t]) - st.mean(b[t]) for t in ts) if ts else float("nan")


def perm_greater(a, b, rng):
    """One-sided p for stat(a, b) > 0, labels shuffled within each task."""
    obs = stat(a, b)
    hits = 0
    for _ in range(PERMS):
        pa, pb = {}, {}
        for t in TASKS:
            pool = a[t] + b[t]
            rng.shuffle(pool)
            pa[t], pb[t] = pool[: len(a[t])], pool[len(a[t]):]
        if stat(pa, pb) >= obs - 1e-12:
            hits += 1
    return obs, (hits + 1) / (PERMS + 1)


def boot(a, b, rng):
    vals = []
    for _ in range(BOOTS):
        ra = {t: [rng.choice(a[t]) for _ in a[t]] for t in TASKS}
        rb = {t: [rng.choice(b[t]) for _ in b[t]] for t in TASKS}
        vals.append(stat(ra, rb))
    vals.sort()
    return vals[int(0.025 * BOOTS)], vals[int(0.975 * BOOTS) - 1]


def fmt_pts(x):
    return f"{x * 100:+.1f} points"


def main(out):
    runs = load(out)
    rng = random.Random(SEED)
    print("# okf-local: analysis\n")
    print(f"{len(runs)} runs from `{out}`. A pass means the run finished and its hidden test passed.\n")

    print("## Passes by arm and task (higher is better)\n")
    print("| Task | " + " | ".join(f"`{a}` local" for a in ARMS) + " | " + " | ".join(f"`{a}` hosted" for a in ARMS) + " |")
    print("| --- |" + " --- |" * 6)
    for i, t in enumerate(TASKS):
        cells = []
        for a in ARMS:
            v = by_task(runs, a, "pass")[t]
            cells.append(f"{sum(v)}/{len(v)}")
        cells += [f"{HOSTED[a][i]}/5" for a in ARMS]
        print(f"| {t} | " + " | ".join(cells) + " |")
    tot = [f"**{sum(r['pass'] for r in runs if r['arm'] == a)}/{sum(1 for r in runs if r['arm'] == a)}**" for a in ARMS]
    print("| **Total** | " + " | ".join(tot) + " | " + " | ".join(f"**{sum(HOSTED[a])}/20**" for a in ARMS) + " |\n")

    print("## Hypotheses (one-sided, Holm-adjusted together)\n")
    print("Effect: the mean over tasks of the difference in pass rate (points), or in mean wall time (seconds; negative means `okf` is faster).\n")
    hyp = [
        ("H1", "`okf` passes more than `no_okf`", "okf", "no_okf", "pass", 1),
        ("H2", "`okf` passes more than `source`", "okf", "source", "pass", 1),
        ("H3", "`okf` runs take less wall time than `source`", "okf", "source", "seconds", -1),
    ]
    res = []
    for hid, text, x, y, key, sign in hyp:
        a, b = by_task(runs, x, key), by_task(runs, y, key)
        if sign < 0:
            na, nb = {t: [-v for v in a[t]] for t in TASKS}, {t: [-v for v in b[t]] for t in TASKS}
            _, p = perm_greater(na, nb, rng)
        else:
            _, p = perm_greater(a, b, rng)
        eff = stat(a, b)
        lo, hi = boot(a, b, rng)
        res.append((hid, text, key, eff, lo, hi, p))
    adj = holm([r[-1] for r in res])
    print("| # | Hypothesis | Effect (95% interval) | p | Holm p | Verdict |")
    print("| --- | --- | --- | --- | --- | --- |")
    for (hid, text, key, eff, lo, hi, p), q in zip(res, adj):
        e = f"{fmt_pts(eff)} ({fmt_pts(lo)} to {fmt_pts(hi)})" if key == "pass" else f"{eff:+.0f} s ({lo:+.0f} to {hi:+.0f})"
        verdict = "confirmed" if q < 0.05 else "no measurable difference"
        print(f"| {hid} | {text} | {e} | {p:.4f} | {q:.4f} | {verdict} |")
    print()

    print("## Did the arms happen as designed?\n")
    for a, what in [("okf", "opened the guide"), ("source", "read the backend")]:
        rs = [r for r in runs if r["arm"] == a]
        n = sum(r["used"] for r in rs)
        ok = rs and n >= 0.75 * len(rs)
        print(f"- `{a}`: {n} of {len(rs)} runs {what}{'' if ok else ' (fewer than three quarters: the arm did not happen as designed)'}.")
    left = [f"{r['task']} {r['arm']} {r['rep']}" for r in runs if r["left_workspace"]]
    print(f"- Runs that reached outside what their arm allows: {len(left)}{' (' + ', '.join(left) + ')' if left else ''}.\n")

    print("## Secondary (not tested)\n")
    a, b = by_task(runs, "source", "pass"), by_task(runs, "no_okf", "pass")
    print(f"- `source` against `no_okf`, passes: {fmt_pts(stat(a, b))}.\n")
    print("| Arm | Runs | Timeouts | Correct but timed out | Median wall time (lower is better) | Median tokens (lower is better) | Median turns | Mean energy per run, Wh (lower is better) | Energy cost per run |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for arm in ARMS:
        rs = [r for r in runs if r["arm"] == arm]
        if not rs:
            continue
        wh = [r["wh"] for r in rs if r["wh"] is not None]
        tok = [r["tokens"] for r in rs if r["tokens"]]
        mwh = st.mean(wh) if wh else None
        print(f"| `{arm}` | {len(rs)} | {sum(r['status'] == 'timeout' for r in rs)} | {sum(r['timeout_correct'] for r in rs)} | "
              f"{st.median(r['seconds'] for r in rs) / 60:.1f} min | {st.median(tok) / 1000:.0f}k | {st.median(r['turns'] or 0 for r in rs):.0f} | "
              + (f"{mwh:.1f} | £{mwh / 1000 * PRICE_KWH:.3f} |" if mwh is not None else "n/a | n/a |"))
    print("\nHosted test G for comparison: median time per run 38 to 45 s; tokens per run 294k (`no_okf`), 301k (`okf`), 333k (`source`).")


if __name__ == "__main__":
    main(sys.argv[1])
