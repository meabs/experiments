"""Analysis for 2026-11-design-factory (README "Analysis"). Reads a stage folder and writes analysis.md and
analysis.json into it.

Inputs: <stage>/<arm>/runs/<brief>/<arm>/codex/<rep>/run.json (tokens, seconds, final message), files.txt;
<stage>/eval/<brief>/<arm>/<rep>/eval.json (shoot.py); <stage>/pairs-<judge>.jsonl (judge_pairs.py);
<stage>/states-<judge>.jsonl (judge_states.py) and <stage>/states-overrides.json (hand checks).
Unit of analysis: the pair (plain run i and factory run i of the same brief). Arm A = plain, B = factory.

Usage: python3 -I analyse.py <stage dir>
"""
import json, random, re, sys
from math import comb
from pathlib import Path

JUDGES = ["google/gemini-4-argon", "anthropic/claude-sonnet-5.5"]
CRIT = ["overall", "hierarchy", "polish", "identity", "content", "trust", "journey"]
PRICE = (0.20, 0.02, 1.20)  # gpt-5.6-luna, $ per million tokens: input, cached input, output (OpenAI price list, 5 Nov 2026)


def slug(m):
    return re.sub(r"[^a-z0-9]+", "-", m.lower()).strip("-")


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def signflip(d, seed=1, n=10000):
    """Two-sided sign-flip permutation test that the mean of d is 0 (exact when 2^len(d) <= n)."""
    d = [x for x in d if x == x]
    if not d or all(x == 0 for x in d):
        return 1.0
    obs = abs(mean(d))
    k = len(d)
    if 2 ** k <= n:
        hits = sum(abs(mean([x if (m >> i) & 1 else -x for i, x in enumerate(d)])) >= obs - 1e-12 for m in range(2 ** k))
        return hits / 2 ** k
    rng = random.Random(seed)
    hits = sum(abs(mean([x if rng.random() < 0.5 else -x for x in d])) >= obs - 1e-12 for _ in range(n))
    return (hits + 1) / (n + 1)


def boot(d, seed=1, n=10000):
    d = [x for x in d if x == x]
    if not d:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    ms = sorted(mean(rng.choices(d, k=len(d))) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = max(w, l)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, ps[i] * (len(ps) - rank)))
        out[i] = run
    return out


def cost(tok):
    inp, cached, out = tok.get("input", 0), tok.get("cache_read", 0), tok.get("output", 0)
    return ((inp - cached) * PRICE[0] + cached * PRICE[1] + out * PRICE[2]) / 1e6


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"] +
                     ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def pct(x):
    return "-" if x != x else f"{100 * x:.0f}%"


def load(stage):
    runs = {}
    for rj in sorted(stage.glob("*/runs/*/*/codex/*/run.json")):
        brief, arm, rep = rj.parts[-5], rj.parts[-4], rj.parts[-2]
        r = json.loads(rj.read_text())
        files = (rj.parent / "files.txt").read_text().split() if (rj.parent / "files.txt").exists() else []
        ev = stage / "eval" / brief / arm / rep / "eval.json"
        e = json.loads(ev.read_text()) if ev.exists() else {"screens": [], "contract_error": "not measured"}
        sc = [s for s in e["screens"] if "error" not in s and s.get("png")]
        sizes = [z for s in sc for z in s.get("sizes", []) if not z["inline"]]
        text = " ".join(s.get("text", "") for s in sc)
        rf = rj.parent / "artefacts" / "research.md"
        rtext = rf.read_text(errors="replace") if rf.exists() else ""
        runs[(brief, arm, rep)] = {
            "research_words": len(rtext.split()), "research_sources": len(set(re.findall(r"https?://[^\s)>\]]+", rtext))),
            "brief": brief, "arm": arm, "rep": rep, "seconds": r.get("seconds"), "tokens": r.get("tokens") or {},
            "status": r.get("status"), "answer": r.get("answer") or "", "files": files,
            "design_files": sorted(f for f in files if f.startswith("design/")),
            "contract": e.get("contract_error") is None and bool(sc), "screens": len(sc),
            "distinct": e.get("distinct_screens", 0),
            "axe_per_screen": mean(len(s.get("axe", [])) for s in sc) if sc else float("nan"),
            "axe_clean": mean(1.0 if not s.get("axe") else 0.0 for s in sc) if sc else float("nan"),
            "axe_rules": sorted({a["id"] for s in sc for a in s.get("axe", [])}),
            "overflow": mean(1.0 if s.get("overflow_320", 0) > 1 else 0.0 for s in sc) if sc else float("nan"),
            "t24": mean(1.0 if min(z["w"], z["h"]) >= 24 else 0.0 for z in sizes) if sizes else float("nan"),
            "t44": mean(1.0 if min(z["w"], z["h"]) >= 44 else 0.0 for z in sizes) if sizes else float("nan"),
            "unreachable": sum(len(s.get("unreachable", [])) for s in sc),
            "h1_ok": mean(1.0 if s.get("h1") == 1 else 0.0 for s in sc) if sc else float("nan"),
            "console_errors": sum(len(s.get("console_errors", [])) for s in sc),
            "claims": sorted(set(m.lower() for m in re.findall(r"wcag[^.\n]{0,60}|accessib\w+[^.\n]{0,40}|complian\w+[^.\n]{0,40}", r.get("answer") or "", re.I))),
            "fscs": sorted(set(re.findall(r"£\s?(85,000|120,000)", text))) if brief == "D2" else [],
        }
    return runs


def load_pairs(stage):
    votes = {}  # (brief, rep, view, criterion) -> list of scores for the factory (1, 0, .5)
    raw = []
    for j in JUDGES:
        f = stage / f"pairs-{slug(j)}.jsonl"
        if not f.exists():
            continue
        last = {}
        for line in f.open():
            r = json.loads(line)
            if "error" not in r:
                last[(r["brief"], r["rep"], r["view"], r["first"])] = r
        for (brief, rep, view, first), r in last.items():
            raw.append(r)
            for c in CRIT:
                if c in r:
                    v = r[c]
                    fac = 0.5 if v == "tie" else (1.0 if (v == "1") == (first == "B") else 0.0)
                    votes.setdefault((brief, rep, view, c), []).append(fac)
    return votes, raw


def load_states(stage):
    f = stage / f"states-{slug(JUDGES[0])}.jsonl"
    over = json.loads((stage / "states-overrides.json").read_text()) if (stage / "states-overrides.json").exists() else {}
    out = {}
    if f.exists():
        for line in f.open():
            r = json.loads(line)
            if "error" in r:
                continue
            items = {i["id"]: bool(i["present"]) for i in r["items"]}
            items.update(over.get(r["run"], {}))
            out[(r["brief"], r["arm"], r["rep"])] = items
    return out


def load_research(stage):
    f = stage / f"research-{slug(JUDGES[0])}.jsonl"
    out = {}
    if f.exists():
        for line in f.open():
            r = json.loads(line)
            if "error" in r:
                continue
            d = r.get("decisions", [])
            out[(r["brief"], r["arm"], r["rep"])] = {"n": len(d), "applied": sum(1 for x in d if x.get("applied")),
                                                      "specific": bool(r.get("specific"))}
    return out


def main(stage):
    stage = Path(stage)
    key = json.load(open(Path(__file__).resolve().parent.parent / "key" / "states.json"))["briefs"]
    kind = {i["id"]: i["kind"] for b in key.values() for i in b}
    runs, (votes, raw), states, rsch = load(stage), load_pairs(stage), load_states(stage), load_research(stage)
    briefs = sorted({k[0] for k in runs})
    pairs = sorted({(b, r) for (b, a, r) in runs if (b, "A", r) in runs and (b, "B", r) in runs})
    md, js = [f"# Analysis: {stage.name}", "", f"{len(runs)} runs, {len(pairs)} pairs (plain run i with factory run i of the same brief). "
              "A = plain agent, B = Design Factory.", ""], {"pairs": len(pairs)}

    def pair_score(b, r, view, c="overall"):
        a_ok, b_ok = runs[(b, "A", r)]["screens"] > 0, runs[(b, "B", r)]["screens"] > 0
        if not a_ok or not b_ok:  # a run with nothing to show loses the pair; both empty is a tie
            return 0.5 if a_ok == b_ok else (1.0 if b_ok else 0.0)
        v = votes.get((b, r, view, c))
        return mean(v) if v else float("nan")

    tests = []
    for view, label in (("whole", "H1 whole design"), ("looks", "H2 looks only (first six screens)")):
        s = [pair_score(b, r, view) for b, r in pairs]
        s = [x for x in s if x == x]
        w, l, t = sum(x > 0.5 for x in s), sum(x < 0.5 for x in s), sum(x == 0.5 for x in s)
        d = [x - 0.5 for x in s]
        tests.append({"h": label, "n": len(s), "factory_wins": w, "plain_wins": l, "ties": t, "mean_score": mean(s),
                      "ci": [x + 0.5 for x in boot(d)], "p_sign": sign_test(w, l), "p": signflip(d)})

    def paired(field, label, source=None):
        d = []
        for b, r in pairs:
            x, y = (source or (lambda k: runs[k][field]))((b, "A", r)), (source or (lambda k: runs[k][field]))((b, "B", r))
            if x == x and y == y and x is not None and y is not None:
                d.append(y - x)
        a = mean((source or (lambda k: runs[k][field]))(k) for k in runs if k[1] == "A" and (source or (lambda k: runs[k][field]))(k) == (source or (lambda k: runs[k][field]))(k))
        bb = mean((source or (lambda k: runs[k][field]))(k) for k in runs if k[1] == "B" and (source or (lambda k: runs[k][field]))(k) == (source or (lambda k: runs[k][field]))(k))
        return {"h": label, "n": len(d), "plain": a, "factory": bb, "diff": mean(d), "ci": list(boot(d)), "p": signflip(d)}

    def share(k, only=None):
        it = states.get(k)
        if it is None:
            return float("nan")
        ids = [i for i in it if only is None or kind[i] == only]
        return mean(1.0 if it[i] else 0.0 for i in ids)

    h3 = paired(None, "H3 checklist items present (share of 12)", share)
    h4 = paired("axe_per_screen", "H4 axe rule violations per screen (lower is better)")
    for t, p in zip(tests + [h3, h4], holm([t["p"] for t in tests] + [h3["p"], h4["p"]])):
        t["p_holm"] = p
    def applied(k):
        r = rsch.get(k)
        return (r["applied"] / r["n"] if r and r["n"] else 0.0) if r is not None else float("nan")

    h6 = paired(None, "H6 research decisions visibly applied in the storyboard (share)", applied)
    h6["p_holm"] = holm([t["p"] for t in tests] + [h3["p"], h4["p"], h6["p"]])[-1]
    js["tests"] = tests + [h3, h4, h6]

    md += ["## Which design do the judges prefer?", "",
           "Each pair gets a score from 0 to 1: the share of its judge votes (two judges, two orders) that chose the "
           "factory's design; a tie counts half. Above 0.5 the factory wins the pair, below 0.5 the plain agent does. "
           "0.5 overall means no preference. p is a two-sided sign-flip permutation test on the pair scores; the sign "
           "test counts wins only.", "",
           table(["Question", "Pairs", "Factory wins", "Plain wins", "Split", "Mean score (95% CI)", "p", "Holm p", "Sign test p"],
                 [[t["h"], t["n"], t["factory_wins"], t["plain_wins"], t["ties"],
                   f"{t['mean_score']:.2f} ({t['ci'][0]:.2f} to {t['ci'][1]:.2f})", f"{t['p']:.4f}", f"{t['p_holm']:.4f}", f"{t['p_sign']:.4f}"] for t in tests]), ""]

    rows = []
    for c in CRIT:
        row = [c]
        for view in ("whole", "looks"):
            s = [pair_score(b, r, view, c) for b, r in pairs]
            s = [x for x in s if x == x]
            row.append(f"{mean(s):.2f}" if s else "-")
        rows.append(row)
    md += ["### By criterion (mean pair score; above 0.5 favours the factory; descriptive)", "",
           table(["Criterion", "Whole design", "Looks only"], rows), ""]
    rows = []
    for b in briefs:
        row = [b]
        for view in ("whole", "looks"):
            s = [pair_score(bb, r, view) for bb, r in pairs if bb == b]
            s = [x for x in s if x == x]
            row += [f"{mean(s):.2f}" if s else "-", f"{sum(x > .5 for x in s)}-{sum(x < .5 for x in s)}-{sum(x == .5 for x in s)}"]
        rows.append(row)
    md += ["### By brief (mean pair score; factory wins-plain wins-split)", "",
           table(["Brief", "Whole: score", "Whole: W-L-S", "Looks: score", "Looks: W-L-S"], rows), ""]

    # judges: position bias and agreement
    rows = []
    for j in JUDGES:
        rj = [r for r in raw if r["judge"] == j]
        if not rj:
            continue
        first = mean(1.0 if r["overall"] == "1" else 0.0 for r in rj if r["overall"] != "tie")
        fac = mean(0.5 if r["overall"] == "tie" else (1.0 if (r["overall"] == "1") == (r["first"] == "B") else 0.0) for r in rj)
        by = {}
        for r in rj:
            by.setdefault((r["brief"], r["rep"], r["view"]), {})[r["first"]] = 0.5 if r["overall"] == "tie" else (1.0 if (r["overall"] == "1") == (r["first"] == "B") else 0.0)
        cons = mean(1.0 if v.get("A") == v.get("B") else 0.0 for v in by.values() if len(v) == 2)
        rows.append([j, len(rj), pct(first), pct(cons), f"{fac:.2f}"])
    md += ["### The judges", "",
           "Chose the first design shown: 50% means no position bias. Same choice in both orders: how often a judge "
           "picked the same design whichever came first (a pair where it flips counts as a split).", "",
           table(["Judge", "Calls", "Chose the design shown first", "Same choice in both orders", "Mean vote for factory"], rows), ""]
    if len([j for j in JUDGES if any(r["judge"] == j for r in raw)]) == 2:
        agree = []
        for b, r in pairs:
            for view in ("whole", "looks"):
                per = []
                for j in JUDGES:
                    v = [0.5 if x["overall"] == "tie" else (1.0 if (x["overall"] == "1") == (x["first"] == "B") else 0.0)
                         for x in raw if x["judge"] == j and (x["brief"], x["rep"], x["view"]) == (b, r, view)]
                    if v:
                        per.append(mean(v))
                if len(per) == 2:
                    agree.append(1.0 if (per[0] > .5) == (per[1] > .5) and (per[0] < .5) == (per[1] < .5) else 0.0)
        md += [f"The two judges reached the same pair result (factory, plain or split) in {pct(mean(agree))} of {len(agree)} pair-views.", ""]

    md += ["## Checklist, accessibility checks", "",
           "Checklist: share of the brief's 12 checklist items visible in the storyboard's text (higher is better). "
           "axe: WCAG A and AA rule violations found by axe-core per screen (lower is better). Difference = factory "
           "minus plain, per pair.", "",
           table(["Measure", "Pairs", "Plain", "Factory", "Difference (95% CI)", "p", "Holm p"],
                 [[t["h"], t["n"], f"{t['plain']:.2f}", f"{t['factory']:.2f}", f"{t['diff']:+.2f} ({t['ci'][0]:+.2f} to {t['ci'][1]:+.2f})",
                   f"{t['p']:.4f}", f"{t['p_holm']:.4f}"] for t in (h3, h4)]), ""]
    if rsch:
        rows = []
        for a, name in (("A", "Plain"), ("B", "Factory")):
            x = [v for k, v in rsch.items() if k[1] == a]
            rows.append([name, len(x), f"{mean(v['n'] for v in x):.1f}", pct(mean((v['applied'] / v['n']) if v['n'] else 0.0 for v in x)),
                         pct(mean(1.0 if v['specific'] else 0.0 for v in x))])
        md += ["## Does the design apply the research?", "",
               "A vision model (blind to the arm) reads each run's research.md and looks at its frames. Decisions listed = the "
               "numbered design decisions the agent wrote; applied = visibly shown in a frame (higher is better); a run that "
               "listed no decisions scores 0. Specific = names current trends or styles with sources.", "",
               table(["Arm", "Runs", "Decisions listed per run", "Share applied", "Research is specific"], rows),
               "", table(["Measure", "Pairs", "Plain", "Factory", "Difference (95% CI)", "p", "Holm p"],
                         [[h6["h"], h6["n"], f"{h6['plain']:.2f}", f"{h6['factory']:.2f}", f"{h6['diff']:+.2f} ({h6['ci'][0]:+.2f} to {h6['ci'][1]:+.2f})", f"{h6['p']:.4f}", f"{h6['p_holm']:.4f}"]]), ""]
    desc = [("Checklist: 'state' items present", lambda k: share(k, "state"), pct), ("Checklist: 'info' items present", lambda k: share(k, "info"), pct),
            ("Screens delivered", lambda k: runs[k]["screens"], lambda x: f"{x:.1f}"),
            ("Delivery contract met (screens.json and every screen opens)", lambda k: 1.0 if runs[k]["contract"] else 0.0, pct),
            ("Screens with no axe violation", lambda k: runs[k]["axe_clean"], pct),
            ("Screens that scroll sideways at 320 px (lower is better)", lambda k: runs[k]["overflow"], pct),
            ("Controls at least 24 px in both directions", lambda k: runs[k]["t24"], pct),
            ("Controls at least 44 px in both directions", lambda k: runs[k]["t44"], pct),
            ("Screens with exactly one h1", lambda k: runs[k]["h1_ok"], pct),
            ("Clickable things not reachable by keyboard, per run (lower is better)", lambda k: runs[k]["unreachable"], lambda x: f"{x:.1f}"),
            ("Console errors per run (lower is better)", lambda k: runs[k]["console_errors"], lambda x: f"{x:.1f}")]
    rows = []
    for label, fn, fmt in desc:
        va = [fn(k) for k in runs if k[1] == "A"]
        vb = [fn(k) for k in runs if k[1] == "B"]
        rows.append([label, fmt(mean(x for x in va if x == x)), fmt(mean(x for x in vb if x == x))])
    md += ["### Descriptive measures (means over runs; no tests)", "", table(["Measure", "Plain", "Factory"], rows), ""]
    rows = []
    for b in briefs:
        rows.append([b] + [f"{mean(x for x in (share((b, a, r)) for (bb, aa, r) in runs if bb == b and aa == a) if x == x) * 12:.1f}" for a in "AB"]
                    + [f"{mean(runs[k]['axe_per_screen'] for k in runs if k[0] == b and k[1] == a and runs[k]['axe_per_screen'] == runs[k]['axe_per_screen']):.2f}" for a in "AB"]
                    + [f"{mean(runs[k]['screens'] for k in runs if k[0] == b and k[1] == a):.1f}" for a in "AB"])
    md += ["### By brief", "", table(["Brief", "Checklist of 12: plain", "factory", "axe per screen: plain", "factory", "Screens: plain", "factory"], rows), ""]
    if states:
        rows = []
        for b in briefs:
            for i in key[b]:
                pa = [states[k][i["id"]] for k in states if k[0] == b and k[1] == "A" and i["id"] in states[k]]
                pb = [states[k][i["id"]] for k in states if k[0] == b and k[1] == "B" and i["id"] in states[k]]
                rows.append([i["id"], i["kind"], i["item"][:90], f"{sum(pa)}/{len(pa)}", f"{sum(pb)}/{len(pb)}"])
        md += ["### Every checklist item (runs in which it was present)", "", table(["Item", "Kind", "What", "Plain", "Factory"], rows), ""]
    rules = {}
    for k, r in runs.items():
        for x in r["axe_rules"]:
            rules.setdefault(x, {"A": 0, "B": 0})[k[1]] += 1
    md += ["### axe rules violated (number of runs with at least one violation)", "",
           table(["Rule", "Plain", "Factory"], [[x, v["A"], v["B"]] for x, v in sorted(rules.items())] or [["none", 0, 0]]), ""]

    md += ["## Cost and process", "",
           "Tokens and seconds are means per run (lower is cheaper). Cost at gpt-5.6-luna list prices.", ""]
    rows = []
    for a, name in (("A", "Plain"), ("B", "Factory")):
        x = [r for k, r in runs.items() if k[1] == a]
        rows.append([name, len(x), f"{mean(r['tokens'].get('input', 0) for r in x) / 1000:.0f}k",
                     f"{mean(r['tokens'].get('cache_read', 0) for r in x) / 1000:.0f}k", f"{mean(r['tokens'].get('output', 0) for r in x) / 1000:.1f}k",
                     f"{mean(r['seconds'] or 0 for r in x):.0f}", f"${mean(cost(r['tokens']) for r in x):.3f}",
                     f"{mean(len(r['design_files']) for r in x):.1f}", f"{mean(r['research_words'] for r in x):.0f}", f"{mean(r['research_sources'] for r in x):.1f}", sum(1 for r in x if r["claims"])])
    md += [table(["Arm", "Runs", "Input tokens", "of which cached", "Output tokens", "Seconds", "Cost per run", "Design files written", "research.md words", "Distinct URLs in research.md", "Runs whose final message mentions accessibility, WCAG or compliance"], rows), ""]
    fs = [(k, r["fscs"]) for k, r in runs.items() if k[0] == "D2"]
    if fs:
        md += ["FSCS limit shown in D2 storyboards (the limit has been £120,000 since 1 December 2025): " +
               "; ".join(f"{'plain' if a == 'A' else 'factory'}: " + ", ".join(f"£{v} in {sum(1 for k, f in fs if k[1] == a and v in f)}" for v in ("85,000", "120,000")) +
                         f", none in {sum(1 for k, f in fs if k[1] == a and not f)}" for a in "AB") + " runs.", ""]
    js["runs"] = {"/".join(k): {x: v for x, v in r.items() if x not in ("answer",)} for k, r in runs.items()}
    (stage / "analysis.md").write_text("\n".join(md) + "\n")
    (stage / "analysis.json").write_text(json.dumps(js, indent=1, default=str))
    print("\n".join(md[:14]))


if __name__ == "__main__":
    main(sys.argv[1])
