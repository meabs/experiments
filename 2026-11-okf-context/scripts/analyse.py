"""Analysis for okf-context (README "Prediction and hypotheses" and "Detailed analysis plan"). Reads a stage
directory (results/pilot or results/main): the feature grades (grade.json), the FMEA judge file(s), the transcripts
file (scripts/transcripts.py) and the run records, applies my judge overrides, and writes <stage>/analysis.md and
<stage>/analysis.json.

Pre-registered: H1 (TOST on B - A feature pass rate, 90% hierarchical bootstrap, +-15 points), H2-H7 (permutation
tests, 10,000 permutations, seed 1, Holm-adjusted together at 0.05). Everything else is descriptive or exploratory
and labelled so.
Usage: python3 -I analyse.py <stage dir> [--judge google/gemini-4-argon] [--second anthropic/claude-sonnet-5.5]
"""
import json, math, random, re, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path

E = Path(__file__).resolve().parent.parent
KEY = {e["id"]: e for e in json.load(open(E / "key" / "fmea_key.json"))["entries"]}
FEATURES = ["F1", "F2", "F3", "F6", "F7"]  # F4 and F5 retired after the pilot (amendment 1)
IN_CODE_TICKETS, CONTEXT_TICKETS = ["F1", "F2", "F3"], ["F6", "F7"]
ARMS = ["A", "B", "C"]
N_PERM = N_BOOT = 10000
DEPENDANTS = ["customers", "back-office staff", "finance reconciliation", "fraud team", "regulatory reporting",
              "regulator", "complaints", "operations", "core ledger"]


def slug(m):
    return re.sub(r"[^a-z0-9]+", "-", m.lower()).strip("-")


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def perm_test(a, b, stat=lambda a, b: mean(b) - mean(a), alternative="greater", seed=1):
    """Permutation test of stat(a, b) (default: mean(b) - mean(a)). alternative: greater | two-sided."""
    rng = random.Random(seed)
    obs = stat(a, b)
    pooled, na = a + b, len(a)
    hits = 0
    for _ in range(N_PERM):
        rng.shuffle(pooled)
        s = stat(pooled[:na], pooled[na:])
        hits += (s >= obs - 1e-12) if alternative == "greater" else (abs(s) >= abs(obs) - 1e-12)
    return obs, (hits + 1) / (N_PERM + 1)


def boot_ci(a, b, level=0.95, seed=1, stat=lambda a, b: mean(b) - mean(a)):
    rng = random.Random(seed)
    xs = sorted(stat([rng.choice(a) for _ in a], [rng.choice(b) for _ in b]) for _ in range(N_BOOT))
    lo = xs[int((1 - level) / 2 * N_BOOT)]
    hi = xs[int((1 + level) / 2 * N_BOOT) - 1]
    return lo, hi


def boot_hier(byticket_a, byticket_b, level=0.90, seed=1):
    """B - A pass rate, resampling tickets, then runs within each ticket (README H1)."""
    rng = random.Random(seed)
    tickets = sorted(set(byticket_a) & set(byticket_b))
    xs = []
    for _ in range(N_BOOT):
        ts = [rng.choice(tickets) for _ in tickets]
        da = [mean([rng.choice(byticket_a[t]) for _ in byticket_a[t]]) for t in ts]
        db = [mean([rng.choice(byticket_b[t]) for _ in byticket_b[t]]) for t in ts]
        xs.append(mean(db) - mean(da))
    xs.sort()
    return xs[int((1 - level) / 2 * N_BOOT)], xs[int((1 + level) / 2 * N_BOOT) - 1]


def holm(ps):
    order = sorted(ps, key=lambda k: ps[k])
    adj, running = {}, 0
    for i, k in enumerate(order):
        running = max(running, min(1, (len(ps) - i) * ps[k]))
        adj[k] = running
    return adj


def spearman(x, y):
    if len(x) < 3:
        return None
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
                j += 1
            for k in range(i, j + 1):
                r[s[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else None


# ---------------------------------------------------------------- loading
def load_features(stage):
    rows = []
    for g in sorted(stage.glob("feat-*/runs/*/*/codex/*/grade.json")):
        task, arm, rep = g.parts[-5], g.parts[-4], int(g.parts[-2])
        if task not in FEATURES:
            continue
        d = json.load(open(g))
        run = json.load(open(g.parent / "run.json"))
        hr = d.get("hidden_results", {})
        integ = [v for k, v in hr.items() if k.startswith("integration_")]
        func = [v for k, v in hr.items() if not k.startswith("integration_")]
        rows.append({"task": task, "arm": arm, "rep": rep, "pass": int(bool(d["pass"])), "build": d["build"],
                     "regression_ok": d["regression"]["passed"] == d["regression"]["total"] and d["build"],
                     "integration_ok": (all(integ) and d["build"]) if integ else None,
                     "ticket_ok": all(func) and d["build"] and bool(func), "hidden": hr,
                     "failed": d.get("failed", []), "status": run.get("status"), "seconds": run.get("seconds"),
                     "tokens": run.get("tokens") or {}, "protected": (g.parent / "protected.txt").read_text().split()})
    return rows


def load_judge(stage, model, overrides):
    f = stage / f"judge-{slug(model)}.jsonl"
    if not f.exists():
        return {}
    out = {}
    for j in map(json.loads, f.open()):
        if "error" in j:
            continue
        out[j["run"]] = j
    for run, fixes in overrides.items():  # {"B/3": {"K04": {"lenient": false}, "invented_remove": [0]}, ...}
        if run in out:
            for k in out[run]["key"]:
                if k["id"] in fixes:
                    k.update(fixes[k["id"]])
            drop = set(fixes.get("invented_remove", []))
            out[run]["invented"] = [x for i, x in enumerate(out[run].get("invented", [])) if i not in drop]
    return out


def fmea_rows(judge, transcripts, stage):
    rows = []
    for run, j in judge.items():
        arm, rep = run.split("/")
        keyd = {k["id"]: k for k in j["key"]}
        def recall(ids, field="lenient"):
            ids = list(ids)
            return mean([1.0 if keyd[i].get(field) else 0.0 for i in ids]) if ids else float("nan")
        text = (stage / f"fmea-{arm}/runs/FMEA/{arm}/codex/{rep}/fmea.md").read_text(errors="replace")
        run_json = json.load(open(stage / f"fmea-{arm}/runs/FMEA/{arm}/codex/{rep}/run.json"))
        rows.append({
            "arm": arm, "rep": int(rep), "words": j.get("words"), "rows": j.get("rows"),
            "recall": recall(KEY), "recall_strict": recall(KEY, "strict"),
            "recall_context": recall(i for i in KEY if KEY[i]["source"] == "context_only"),
            "recall_inferable": recall(i for i in KEY if KEY[i]["source"] == "inferable"),
            "recall_in_code": recall(i for i in KEY if KEY[i]["source"] == "in_code"),
            "recall_role": recall(i for i in KEY if KEY[i]["about"] == "role"),
            "recall_internals": recall(i for i in KEY if KEY[i]["about"] == "internals"),
            "recall_high": recall(i for i in KEY if KEY[i]["S"] >= 8),
            "found": {i: bool(keyd[i].get("lenient")) for i in KEY},
            "found_strict": {i: bool(keyd[i].get("strict")) for i in KEY},
            "quality": {i: keyd[i] for i in KEY if keyd[i].get("lenient")},
            "extras": j.get("extras", []), "invented": j.get("invented", []),
            "text": text, "seconds": run_json.get("seconds"), "tokens": run_json.get("tokens") or {},
            "status": run_json.get("status"),
        })
    return rows


# ---------------------------------------------------------------- report helpers
def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.0f}%"


def pts(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:+.0f}"


def by_arm(rows, field):
    return {a: [r[field] for r in rows if r["arm"] == a and r[field] is not None
                and not (isinstance(r[field], float) and math.isnan(r[field]))] for a in ARMS}


def table(head, body):
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in body]
    return "\n".join(out)


def cost_usd(tok):
    # gpt-5.6-luna list price per million tokens (input, cached input, output): see README "Cost".
    PRICE = (1.25, 0.125, 10.0)
    inp, cached, out = tok.get("input", 0), tok.get("cache_read", 0), tok.get("output", 0)
    return ((inp - cached) * PRICE[0] + cached * PRICE[1] + out * PRICE[2]) / 1e6


# ---------------------------------------------------------------- main
def main(stage, judge_model, second_model):
    stage = Path(stage)
    ov_file = stage / "judge-overrides.json"
    overrides = json.load(open(ov_file)) if ov_file.exists() else {}
    feats = load_features(stage)
    tr = [json.loads(l) for l in open(stage / "transcripts.jsonl")] if (stage / "transcripts.jsonl").exists() else []
    judge = load_judge(stage, judge_model, overrides)
    fm = fmea_rows(judge, tr, stage)
    judge2 = load_judge(stage, second_model, {}) if second_model else {}
    fm2 = fmea_rows(judge2, tr, stage) if judge2 else []
    md, res = [f"# okf-context analysis: {stage.name}", "",
               f"Feature runs: {len(feats)}. FMEA reports judged: {len(fm)} (judge `{judge_model}`"
               + (f", hand overrides for {len(overrides)} runs" if overrides else "") + ").", ""], {}

    # ---------- headline
    fp = by_arm(feats, "pass")
    fr = by_arm(fm, "recall")
    md += ["## Headline", "",
           table(["Arm", "Feature changes fully correct (share of runs, higher is better)",
                  "FMEA recall (share of the 22 answer-key failure modes found, mean per run, higher is better)",
                  "Invented facts per FMEA (mean, lower is better)"],
                 [[a, f"{pct(mean(fp[a]))} ({sum(fp[a])}/{len(fp[a])})" if fp[a] else "n/a",
                   f"{pct(mean(fr[a]))} (n={len(fr[a])})" if fr[a] else "n/a",
                   f"{mean([len(r['invented']) for r in fm if r['arm'] == a]):.1f}" if fr[a] else "n/a"] for a in ARMS]), ""]

    # ---------- hypotheses
    hyp, ps = [], {}
    def bt(t, a):
        return [r["pass"] for r in feats if r["task"] == t and r["arm"] == a]
    if fp["A"] and fp["B"]:
        ta = {t: bt(t, "A") for t in FEATURES if bt(t, "A")}
        tb = {t: bt(t, "B") for t in FEATURES if bt(t, "B")}
        d = mean([mean(v) for v in tb.values()]) - mean([mean(v) for v in ta.values()])
        lo, hi = boot_hier(ta, tb)
        verdict = "equivalent within 15 points" if lo > -0.15 and hi < 0.15 else (
            "different" if lo > 0 or hi < 0 else "inconclusive")
        hyp.append(["H1", "features: B - A within +-15 points (TOST)", f"{pts(d)} points", f"90% CI {pts(lo)} to {pts(hi)}",
                    "-", verdict])
        res["H1"] = {"diff": d, "ci90": [lo, hi], "verdict": verdict}
    if fr["A"] and fr["B"]:
        o, p = perm_test(fr["A"], fr["B"]); ps["H2"] = p
        hyp.append(["H2", "FMEA recall B > A", f"{pts(o)} points", "95%% CI %s to %s" % tuple(map(pts, boot_ci(fr["A"], fr["B"]))), f"{p:.4f}", None])
    if fr["A"] and fr["B"] and fp["A"] and fp["B"]:
        # difference of differences: permute arm labels within each task type independently
        rng = random.Random(1)
        obs = (mean(fr["B"]) - mean(fr["A"])) - (mean(fp["B"]) - mean(fp["A"]))
        pf, pa = fr["A"] + fr["B"], fp["A"] + fp["B"]
        hits = 0
        for _ in range(N_PERM):
            rng.shuffle(pf); rng.shuffle(pa)
            s = (mean(pf[len(fr["A"]):]) - mean(pf[:len(fr["A"])])) - (mean(pa[len(fp["A"]):]) - mean(pa[:len(fp["A"])]))
            hits += s >= obs - 1e-12
        p = (hits + 1) / (N_PERM + 1); ps["H3"] = p
        hyp.append(["H3", "OKF benefit larger for FMEA than features", f"{pts(obs)} points", "-", f"{p:.4f}", None])
    inv = {a: [len(r["invented"]) for r in fm if r["arm"] == a] for a in ARMS}
    if inv["A"] and inv["B"]:
        o, p = perm_test(inv["B"], inv["A"]); ps["H4"] = p  # A - B > 0: fewer invented with B
        hyp.append(["H4", "fewer invented facts with B", f"{o:+.2f} per report (A - B)", "-", f"{p:.4f}", None])
    if fp["B"] and fp["C"]:
        o, p = perm_test(fp["B"], fp["C"], alternative="two-sided"); ps["H5-features"] = p
        hyp.append(["H5 (features)", "B and C differ", f"{pts(o)} points (C - B)", "-", f"{p:.4f}", None])
    if fr["B"] and fr["C"]:
        o, p = perm_test(fr["B"], fr["C"], alternative="two-sided"); ps["H5-FMEA"] = p
        hyp.append(["H5 (FMEA)", "B and C differ", f"{pts(o)} points (C - B)", "-", f"{p:.4f}", None])
    for h, hi_f, lo_f, label in (("H6", "recall_context", "recall_in_code", "B's gain larger on context-only than in-code FMEA entries"),
                                 ("H7", "recall_role", "recall_internals", "B's gain larger on role than internals FMEA entries")):
        da = [r[hi_f] - r[lo_f] for r in fm if r["arm"] == "A"]
        db = [r[hi_f] - r[lo_f] for r in fm if r["arm"] == "B"]
        if da and db:
            o, p = perm_test(da, db); ps[h] = p
            hyp.append([h, label, f"{pts(o)} points", "-", f"{p:.4f}", None])
    adj = holm(ps) if ps else {}
    for row in hyp:
        if row[0] in adj:
            row[5] = f"Holm p = {adj[row[0]]:.4f}: " + ("supported" if adj[row[0]] < 0.05 else "not supported")
    res["p"], res["holm"] = ps, adj
    md += ["## Pre-registered hypotheses", "",
           "Differences are B - A unless stated, in percentage points of the measure's 0-100% scale. p values are "
           "one-sided permutation tests (two-sided for H5); H2 to H7 are Holm-adjusted together at 0.05; H1 is an "
           "equivalence test, judged on its own 90% interval.", "",
           table(["#", "Statement", "Observed", "Interval", "p (raw)", "Verdict"], hyp), ""]

    # ---------- part 1: features in depth
    rows = []
    for t in FEATURES:
        r = [t, "in code" if t in IN_CODE_TICKETS else "integration (context only)"]
        for a in ARMS:
            v = bt(t, a)
            r.append(f"{sum(v)}/{len(v)} ({pct(wilson(sum(v), len(v))[0])}-{pct(wilson(sum(v), len(v))[1])})" if v else "-")
        rows.append(r)
    md += ["## 1. Feature changes in depth", "",
           "Fully correct runs per ticket (every hidden test and every existing test passed; Wilson 95% interval; "
           "higher is better).", "", table(["Ticket", "Rules", "A", "B", "C"], rows), ""]
    rows = []
    for t in FEATURES:
        tests = sorted({k for r in feats if r["task"] == t for k in r["hidden"]})
        for k in tests:
            rows.append([t, k] + [f"{sum(r['hidden'].get(k, False) for r in feats if r['task'] == t and r['arm'] == a)}/"
                                  f"{sum(1 for r in feats if r['task'] == t and r['arm'] == a)}" for a in ARMS])
    md += ["Each hidden test: runs that passed it, of runs (higher is better). `integration_` tests check a rule of an "
           "external system's behaviour; builds that failed count as failing every test.", "",
           table(["Ticket", "Hidden test", "A", "B", "C"], rows), ""]
    for half, ts in (("in-code tickets (F1-F3)", IN_CODE_TICKETS), ("integration tickets (F6-F7)", CONTEXT_TICKETS)):
        a_ = [r["pass"] for r in feats if r["task"] in ts and r["arm"] == "A"]
        b_ = [r["pass"] for r in feats if r["task"] in ts and r["arm"] == "B"]
        c_ = [r["pass"] for r in feats if r["task"] in ts and r["arm"] == "C"]
        if a_ and b_:
            ta = {t: bt(t, "A") for t in ts if bt(t, "A")}; tb = {t: bt(t, "B") for t in ts if bt(t, "B")}
            lo, hi = boot_hier(ta, tb) if len(ta) > 1 else boot_ci(a_, b_, 0.90)
            md.append(f"- **{half}**: A {pct(mean(a_))}, B {pct(mean(b_))}, C {pct(mean(c_)) if c_ else 'n/a'}; "
                      f"B - A {pts(mean(b_) - mean(a_))} points, 90% interval {pts(lo)} to {pts(hi)} "
                      "(H1's sensitivity to the ticket mix, section 6).")
    integ = [r for r in feats if r["integration_ok"] is not None]
    if integ:
        md += ["", "Integration rule right (all `integration_` tests passed, F6 and F7; higher is better): " +
               ", ".join(f"{a} {sum(r['integration_ok'] for r in integ if r['arm'] == a)}/"
                         f"{sum(1 for r in integ if r['arm'] == a)}" for a in ARMS) + "."]
    tamper = [f"{r['task']} {r['arm']}/{r['rep']}: {', '.join(r['protected'])}" for r in feats if r["protected"]]
    md += ["", "Runs that changed protected files (the grader restores them): " + ("; ".join(tamper) if tamper else "none") + ".",
           "", "Failure taxonomy (labelled from the diff and transcript by the judge model and me; Cohen's kappa) is "
           "in `results/<stage>/taxonomy.md` once labelled.", ""]

    # ---------- part 2: FMEA in depth
    if fm:
        def row(field, label):
            v = by_arm(fm, field)
            return [label] + [f"{pct(mean(v[a]))} ({pct(min(v[a]))}-{pct(max(v[a]))})" if v[a] else "-" for a in ARMS]
        md += ["## 2. Service FMEA in depth", "",
               "Recall: share of the answer key's failure modes a report contains (mean per run; in brackets the "
               "lowest and highest run; higher is better). Lenient: the same failure mode; strict: the same mode and cause.", "",
               table(["Answer-key entries", "A", "B", "C"], [
                   row("recall", "all 22 (lenient, primary)"), row("recall_strict", "all 22 (strict)"),
                   row("recall_context", "7 context-only"), row("recall_inferable", "5 inferable"),
                   row("recall_in_code", "10 in code"), row("recall_role", "14 about the service's role"),
                   row("recall_internals", "8 about internals"), row("recall_high", "12 high-severity (S >= 8)")]), ""]
        rows = []
        for i, e in KEY.items():
            rows.append([i, e["mode"], e["source"].replace("_", " "), e["about"]] +
                        [f"{sum(r['found'][i] for r in fm if r['arm'] == a)}/{sum(1 for r in fm if r['arm'] == a)}" for a in ARMS])
        md += ["Each answer-key entry: reports that contained it, of reports (higher is better).", "",
               table(["Key", "Failure mode", "Source", "About", "A", "B", "C"], rows), ""]
        qrows = []
        for crit, lab in (("effect_customers", "effect on customers right"), ("cause_plausible", "cause plausible for this code"),
                          ("detection_concrete", "detection method concrete"), ("action_addresses_cause", "action addresses the cause")):
            qrows.append([lab] + [pct(mean([1.0 if q.get(crit) else 0.0 for r in fm if r["arm"] == a for q in r["quality"].values()]))
                                  if any(r["arm"] == a for r in fm) else "-" for a in ARMS])
        qrows.append(["dependants named (share of the key's dependants for the entry)"] + [
            pct(mean([len(set(q.get("dependants_named", [])) & set(KEY[i]["dependants"])) / len(KEY[i]["dependants"])
                      for r in fm if r["arm"] == a for i, q in r["quality"].items()])) if any(r["arm"] == a for r in fm) else "-"
            for a in ARMS])
        md += ["Quality of the matched entries (share of matched entries meeting each criterion; higher is better).", "",
               table(["Criterion", "A", "B", "C"], qrows), ""]
        sp = {a: [] for a in ARMS}
        for r in fm:
            xs, ys = [], []
            for i, q in r["quality"].items():
                if all(isinstance(q.get(k), (int, float)) for k in "SOD"):
                    xs.append(q["S"] * q["O"] * q["D"]); ys.append(KEY[i]["S"] * KEY[i]["O"] * KEY[i]["D"])
            s = spearman(xs, ys)
            if s is not None:
                sp[r["arm"]].append(s)
        md += ["Scoring sense: Spearman rank correlation between a report's risk priority numbers and the key's, over "
               "its matched entries (mean per report; 1 = same order; higher is better): " +
               ", ".join(f"{a} {mean(sp[a]):.2f} (n={len(sp[a])})" for a in ARMS if sp[a]) + ".", ""]
        ic = defaultdict(Counter)
        for r in fm:
            for x in r["invented"]:
                ic[r["arm"]][x.get("class", "?")] += 1
        classes = ["external_system", "rule_or_number", "code_claim", "contradicts_context"]
        md += ["Invented facts by class (total over reports; per 1,000 words in brackets; lower is better).", "",
               table(["Class", "A", "B", "C"], [[c] + [f"{ic[a][c]} ({1000 * ic[a][c] / max(1, sum(r['words'] or 0 for r in fm if r['arm'] == a)):.2f})"
                                                   for a in ARMS] for c in classes]), ""]
        ex = {a: Counter(x.get("verdict") for r in fm if r["arm"] == a for x in r["extras"]) for a in ARMS}
        md += ["Extra failure modes not in the key (mean per report): " + "; ".join(
            f"{a}: valid {ex[a]['valid'] / max(1, len(fr[a])):.1f}, generic {ex[a]['generic'] / max(1, len(fr[a])):.1f}, "
            f"wrong {ex[a]['wrong'] / max(1, len(fr[a])):.1f}" for a in ARMS if fr[a]) +
            ". Valid extras are listed in `extras-valid.md` and reported as gaps in the key, not added to it.", ""]
        with open(stage / "extras-valid.md", "w") as fh:
            for r in sorted(fm, key=lambda r: (r["arm"], r["rep"])):
                for x in r["extras"]:
                    if x.get("verdict") == "valid":
                        fh.write(f"- {r['arm']}/{r['rep']}: {x['row']} ({x.get('reason', '')})\n")
        cov = {a: [] for a in ARMS}
        words = {"customers": r"customer", "back-office staff": r"back.?office|support staff|staff",
                 "finance reconciliation": r"reconcil", "fraud team": r"fraud (team|operations|analyst)",
                 "regulatory reporting": r"regulatory (return|report)", "regulator": r"regulator|FCA",
                 "complaints": r"complaint", "operations": r"\boperations\b|\bops\b", "core ledger": r"ledger"}
        for r in fm:
            cov[r["arm"]].append(sum(bool(re.search(w, r["text"], re.I)) for w in words.values()))
        md += ["*Exploratory.* Dependants mentioned at all (of 9, mean per report; higher is better): " +
               ", ".join(f"{a} {mean(cov[a]):.1f}" for a in ARMS if cov[a]) + ".", "",
               "Structure: words per report " + ", ".join(f"{a} {mean([r['words'] for r in fm if r['arm'] == a]):.0f}"
                                                          for a in ARMS if fr[a]) +
               "; rows per report " + ", ".join(f"{a} {mean([r['rows'] or 0 for r in fm if r['arm'] == a]):.1f}" for a in ARMS if fr[a]) + ".", ""]

        # ---------- part 3: context use and traceability
        facts = {"four hours": r"four hours|4 hours|4h\b", "2 seconds (screening)": r"\b2 ?s(ec(ond)?s?)?\b|two seconds",
                 "FRD-7": r"(?-i:FRD-7)", "fails closed": r"fail(s|ing)? closed", "02:00 balance copy": r"02:00|2 ?am",
                 "07:00 reconciliation": r"07:00|7 ?am", "5th working day": r"5th working day|fifth working day",
                 "8 weeks (complaints)": r"8 weeks|eight weeks", "DT01": r"(?-i:\bDT01\b)", "DUPL": r"(?-i:\bDUPL\b)",
                 "24 hours (ledger)": r"24 hours", "30 days (scheme)": r"30 days", "idempotency": r"idempoten"}
        rows = []
        for name, rx in facts.items():
            rows.append([name] + [f"{sum(bool(re.search(rx, r['text'], re.I)) for r in fm if r['arm'] == a)}/{len(fr[a])}"
                                  if fr[a] else "-" for a in ARMS])
        md += ["## 3. How the agent used the context", "",
               "Traceability: reports containing each distinctive fact of the system context (count of reports). A "
               "fact in an A report came from the code, from general knowledge, or was a guess.", "",
               table(["Fact", "A", "B", "C"], rows), ""]
    if tr:
        rows = []
        for task in FEATURES + ["FMEA"]:
            for a in ARMS:
                t = [x for x in tr if x["task"] == task and x["arm"] == a]
                if not t:
                    continue
                rows.append([task, a, len(t), f"{sum(x['okf_read'] for x in t)}/{len(t)}" if a == "B" else "-",
                             f"{mean([x['commands'] for x in t]):.0f}", f"{mean([x['src_files_opened'] for x in t]):.0f}",
                             f"{mean([x['commands_before_first_edit'] for x in t if x['commands_before_first_edit'] is not None] or [float('nan')]):.0f}",
                             f"{mean([x['seconds'] or 0 for x in t]):.0f}"])
        md += ["Exploration per run (means). Codex puts AGENTS.md into the prompt itself, so C always has its section; "
               "for B, \"read okf\" is whether the run opened the bundle.", "",
               table(["Task", "Arm", "Runs", "Read okf", "Commands", "Source files opened", "Commands before the first edit",
                      "Seconds"], rows), ""]
        okf_files = Counter(f for x in tr if x["arm"] == "B" for f in x["okf_files"])
        md += ["Bundle files opened by B runs (count of runs): " + ", ".join(f"{k} {v}" for k, v in okf_files.most_common()) + ".", ""]
        if fm:
            b = {x["rep"]: x for x in tr if x["task"] == "FMEA" and x["arm"] == "B"}
            read = [r["recall"] for r in fm if r["arm"] == "B" and b.get(r["rep"], {}).get("okf_read")]
            noread = [r["recall"] for r in fm if r["arm"] == "B" and not b.get(r["rep"], {}).get("okf_read")]
            md += [f"*Exploratory (correlation only).* B FMEA recall when the run opened the bundle: {pct(mean(read))} "
                   f"(n={len(read)}); when it didn't: {pct(mean(noread))} (n={len(noread)}).", ""]

    # ---------- part 4 is the C columns throughout; part 5 consistency and cost
    md += ["## 5. Consistency and cost", ""]
    rows = []
    for t in FEATURES:
        rows.append([t] + [("all agree" if len(set(bt(t, a))) == 1 else "mixed") + f" ({sum(bt(t, a))}/{len(bt(t, a))})"
                           if bt(t, a) else "-" for a in ARMS])
    md += [table(["Ticket", "A", "B", "C"], rows), ""]
    if fm:
        md += ["FMEA recall spread (standard deviation over reports, points; lower is steadier): " +
               ", ".join(f"{a} {100 * statistics.pstdev(fr[a]):.1f}" for a in ARMS if len(fr[a]) > 1) + "."]
        sometimes = []
        for i in KEY:
            for a in ARMS:
                n = sum(1 for r in fm if r["arm"] == a)
                k = sum(r["found"][i] for r in fm if r["arm"] == a)
                if n and 0.2 <= k / n <= 0.8:
                    sometimes.append(f"{i} in {a} ({k}/{n})")
        md += ["Entries found only sometimes (20-80% of reports): " + (", ".join(sometimes) or "none") + ".", ""]
    rows = []
    for kind, rs in (("features", feats), ("FMEA", fm)):
        for a in ARMS:
            x = [r for r in rs if r["arm"] == a]
            if not x:
                continue
            c = [cost_usd(r["tokens"]) for r in x]
            good = sum(r["pass"] for r in x) if kind == "features" else sum(sum(r["found"].values()) for r in x)
            rows.append([kind, a, len(x), f"{mean([r['tokens'].get('input', 0) for r in x]) / 1000:.0f}k",
                         f"{mean([r['tokens'].get('output', 0) for r in x]) / 1000:.1f}k", f"{mean([r['seconds'] or 0 for r in x]):.0f}",
                         f"${mean(c):.3f}", f"${sum(c) / good:.3f}" if good else "-"])
    md += ["Cost per run at list price (lower is better). Last column: cost per correct result (per fully correct "
           "feature change; per answer-key entry found).", "",
           table(["Task", "Arm", "Runs", "Input tokens", "Output tokens", "Seconds", "Cost per run", "Cost per correct result"], rows), ""]

    # ---------- part 6: robustness
    if fm2:
        f2 = by_arm(fm2, "recall")
        agree, total = 0, 0
        m2 = {(r["arm"], r["rep"]): r for r in fm2}
        for r in fm:
            o = m2.get((r["arm"], r["rep"]))
            if o:
                for i in KEY:
                    total += 1; agree += r["found"][i] == o["found"][i]
        md += ["## 6. Robustness", "", f"Second judge `{second_model}`: FMEA recall " +
               ", ".join(f"{a} {pct(mean(f2[a]))}" for a in ARMS if f2[a]) +
               (f"; B - A {pts(mean(f2['B']) - mean(f2['A']))} points, one-sided permutation p = {perm_test(f2['A'], f2['B'])[1]:.4f}"
                if f2["A"] and f2["B"] else "") +
               f". Agreement with the primary judge on found / not found: {agree}/{total} entry decisions"
               + (f" ({pct(agree / total)})" if total else "") + ".", ""]
    (stage / "analysis.md").write_text("\n".join(md))
    (stage / "analysis.json").write_text(json.dumps(res, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    a = sys.argv[1:]
    jm, sm = "google/gemini-4-argon", None
    if "--judge" in a:
        i = a.index("--judge"); jm = a[i + 1]; del a[i:i + 2]
    if "--second" in a:
        i = a.index("--second"); sm = a[i + 1]; del a[i:i + 2]
    main(a[0], jm, sm)
