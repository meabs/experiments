"""Writes the report's diagrams (diagrams/*.html, SVG 1800 px wide) from results/main. Render to PNG with
diagrams/render.sh.

Colours in the fixed order A, B, C: #6f8f2f, #1170a0, #d0731f (the palette ELC validated with the dataviz validator,
light mode: lightness, chroma, colour-blind separation, normal-vision floor and contrast all pass). Every bar also
carries its arm's name, so identity never rests on colour alone.

Usage: python3 -I scripts/diagrams.py
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "results/main"
OUT = ROOT / "diagrams"
ARMS = [("A", "A  one agent"), ("B", "B  Machinist single"), ("C", "C  Machinist pipeline")]
COL = {"A": "#6f8f2f", "B": "#1170a0", "C": "#d0731f"}
LIGHT = {"A": "#c9d6ab", "B": "#a9cde0", "C": "#efc9a3"}
HARD = ["CATEGORYDELETE", "CUSTOMERCART", "PRODUCTDELETE", "REVIEWS", "STOCK", "SUPPORTORDERS"]
EASY = ["RETURNS", "VISIBILITY"]
SRC = "Source: github.com/meabs/experiments, 2026-11-asf-1"
PRICE = {"input": 0.20, "cached": 0.02, "output": 1.20}


def page(h, body):
    return (f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{h}" viewBox="0 0 1800 {h}">\n'
            '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1d2a44"/></marker>'
            '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#b4532a"/></marker></defs>\n'
            f'{body}</svg>\n')


def setup():
    s = ['<text x="40" y="62" class="th">Three ways to hand Luna the same ticket</text>',
         '<text x="40" y="102" class="ts">Same model (gpt-5.6-luna, medium effort) in every role, same Codex '
         '0.157.0, same one-commit Shopizer checkout, same ticket text.</text>']
    cols = [("A", "A  one agent", ["One Codex run in a sandbox", "Reads the ticket, edits,", "builds, tests, stops",
                                   "", "Delivers: the changed files", "No GitHub, no review"]),
            ("B", "B  Machinist, single agent", ["Machinist starts one Codex run", "with its own Implement prompt",
                                                 "Agent commits, pushes,", "opens a pull request",
                                                 "Delivers: a PR", "No separate review"]),
            ("C", "C  Machinist, standard pipeline", ["Triage (read-only): brief", "Implement: change + PR",
                                                      "Review (read-only): verdict", "Repair: up to 3 rounds",
                                                      "Delivers: the PR at the end", "Spec stage if triage asks"])]
    x = 40
    for a, title, lines in cols:
        s.append(f'<rect x="{x}" y="140" width="560" height="380" rx="16" fill="#fff" stroke="{COL[a]}" '
                 f'stroke-width="5"/><rect x="{x}" y="140" width="560" height="70" rx="16" fill="{COL[a]}"/>'
                 f'<rect x="{x}" y="190" width="560" height="20" fill="{COL[a]}"/>'
                 f'<text x="{x + 28}" y="188" class="tw">{title}</text>')
        for i, l in enumerate(lines):
            s.append(f'<text x="{x + 28}" y="{262 + i * 42}" class="t">{l}</text>')
        x += 580
    s.append('<rect x="40" y="550" width="1720" height="150" rx="14" class="box"/>'
             '<text x="70" y="600" class="t">• Score: share of hidden acceptance tests passed (9 to 17 a ticket) on '
             'what each arm delivered, graded afterwards.</text>'
             '<text x="70" y="650" class="t">• B and C: a fresh private repository per run, so no run can see '
             'another run\'s work.</text>')
    s.append(f'<text x="1760" y="740" class="tsm" text-anchor="end">{SRC} (README.md)</text>')
    return page(770, "\n".join(s))


def scores(an):
    pt = an["per_ticket"]
    x0, w = 440, 1130
    s = ['<text x="40" y="62" class="th">On hard tickets the pipeline was not clearly better; on easy ones it was</text>',
         '<text x="40" y="102" class="ts">Mean share of hidden tests passed, 4 runs per arm and ticket (higher is '
         'better). Dots: single runs (equal scores overlap).</text>']
    y = 150
    for group, tickets in (("Hard tickets", HARD), ("Easy tickets", EASY)):
        s.append(f'<text x="40" y="{y + 20}" class="th" font-size="32">{group}</text>')
        y += 40
        for t in tickets:
            s.append(f'<text x="40" y="{y + 26}" class="tb">{t}</text>')
            y += 40
            for a, label in ARMS:
                m = pt[t][a]["mean"]
                s.append(f'<text x="{x0 - 20}" y="{y + 22}" class="q" text-anchor="end">{label}</text>'
                         f'<rect x="{x0}" y="{y + 4}" width="{max(4, m * w):.0f}" height="24" rx="4" fill="{COL[a]}"/>'
                         f'<text x="1700" y="{y + 24}" class="q" font-weight="650" text-anchor="end">{m * 100:.0f}%</text>')
                for v in pt[t][a]["scores"]:
                    s.append(f'<circle cx="{x0 + v * w:.0f}" cy="{y + 16}" r="6" fill="#fff" stroke="#1d2a44" '
                             'stroke-width="2.5"/>')
                y += 32
            y += 16
        y += 10
    for k in range(0, 101, 25):
        x = x0 + k / 100 * w
        s.append(f'<line x1="{x:.0f}" y1="190" x2="{x:.0f}" y2="{y - 20}" stroke="#d9d4c7" stroke-width="1.5"/>'
                 f'<text x="{x:.0f}" y="{y + 6}" class="tsm" text-anchor="middle">{k}%</text>')
    pa = an["per_arm"]
    y += 40
    s.append(f'<text x="40" y="{y}" class="t">Hard tickets, mean over tickets: A {pa["A"]["hard_score"]*100:.0f}%, '
             f'B {pa["B"]["hard_score"]*100:.0f}%, C {pa["C"]["hard_score"]*100:.0f}%. C vs A: '
             f'+{an["tests"][0]["diff"]*100:.0f} points, Holm p = {an["tests"][0]["p_holm"]:.2f}, not significant.</text>')
    s.append(f'<text x="1760" y="{y + 40}" class="tsm" text-anchor="end">{SRC} (results/main/analysis.json)</text>')
    return page(y + 70, "\n".join(s))


def pipeline(an, re_):
    hard = [r for r in re_ if r["before"] is not None and r["ticket"] in HARD]
    allr = [r for r in re_ if r["before"] is not None]
    b = sum(r["before"] / r["hidden"] for r in hard) / len(hard)
    a = sum(r["after"] / r["hidden"] for r in hard) / len(hard)
    up = sum(r["after"] > r["before"] for r in allr)
    dn = sum(r["after"] < r["before"] for r in allr)
    st = an["per_arm"]["C"]["states"]
    full = an["per_arm"]["C"]["fully_correct"]
    s = ['<text x="40" y="62" class="th">Inside the pipeline: repairs helped a little, and nothing was ever approved</text>',
         '<text x="40" y="102" class="ts">Arm C, 32 runs. Left: hard-ticket score before the first review and at the '
         'end (higher is better). Right: how Machinist ended each job.</text>']
    x0, w = 330, 520
    for i, (lab, v) in enumerate((("Before review", b), ("After repairs", a))):
        y = 170 + i * 70
        s.append(f'<text x="{x0 - 20}" y="{y + 30}" class="t" text-anchor="end">{lab}</text>'
                 f'<rect x="{x0}" y="{y}" width="{v * w:.0f}" height="44" rx="4" fill="{COL["C"] if i else LIGHT["C"]}"/>'
                 f'<text x="{x0 + v * w + 14:.0f}" y="{y + 31}" class="tb">{v * 100:.0f}%</text>')
    s.append(f'<text x="40" y="350" class="t">All 30 runs with a review: {up} improved, {dn} got worse,</text>'
             f'<text x="40" y="392" class="t">{len(allr) - up - dn} unchanged. Arm A scored '
             f'{an["per_arm"]["A"]["hard_score"]*100:.0f}% on the same tickets.</text>')
    x = 960
    s.append(f'<rect x="{x}" y="150" width="800" height="300" rx="14" class="boxr"/>'
             f'<text x="{x + 30}" y="205" class="tb">Machinist\'s end state, 32 jobs</text>'
             f'<text x="{x + 30}" y="260" class="t">blocked (repairs used up, or review blocked): {st.get("blocked", 0)}</text>'
             f'<text x="{x + 30}" y="305" class="t">failed (reply rejected, time-out …): {st.get("failed", 0)}</text>'
             f'<text x="{x + 30}" y="350" class="t">complete, reviewer approved: 0</text>'
             f'<text x="{x + 30}" y="405" class="t red" font-weight="650">Yet {full} of the 32 PRs pass every hidden test.</text>')
    s.append('<rect x="40" y="480" width="1720" height="150" rx="14" class="box"/>'
             '<text x="70" y="530" class="t">• 49 of 87 reviews cite missing CI checks: the repository has no CI, '
             'so the reviewer asks for evidence it can never get.</text>'
             '<text x="70" y="580" class="t">• 7 jobs ended because Luna put one field of its JSON reply in the wrong '
             'place; Machinist\'s strict parser rejected the reply.</text>')
    s.append(f'<text x="1760" y="670" class="tsm" text-anchor="end">{SRC} (results/main/review-effect.json, '
             'machinist-job.json)</text>')
    return page(700, "\n".join(s))


def tokens(an, stages):
    pa = an["per_arm"]
    s = ['<text x="40" y="62" class="th">Tokens per run: the pipeline reads five times as much</text>',
         '<text x="40" y="102" class="ts">Mean input tokens per run, in millions (lower is cheaper); C split by stage. '
         'Right: mean cost per run at Luna\'s list price.</text>']
    x0, scale = 470, 1000 / 12e6
    y = 160
    for a, label in ARMS:
        n = pa[a]["runs"]
        parts = [(a, pa[a]["tokens_per_run"]["input"])] if a != "C" else \
            [(st, stages[("C", st)]["input"] / n) for st in ("triage", "spec", "implement", "review") if ("C", st) in stages]
        s.append(f'<text x="{x0 - 20}" y="{y + 34}" class="t" text-anchor="end">{label}</text>')
        x = x0
        for k, (st, v) in enumerate(parts):
            wd = v * scale
            fill = COL[a] if a != "C" else ("#f5dcc2", "#efc9a3", COL["C"], "#8f4d12")[k % 4]
            s.append(f'<rect x="{x:.0f}" y="{y}" width="{max(2, wd):.0f}" height="50" fill="{fill}" stroke="#fff" stroke-width="2"/>')
            if a == "C" and wd > 90:
                s.append(f'<text x="{x + wd / 2:.0f}" y="{y + 33}" class="q" text-anchor="middle" '
                         f'fill="{"#fff" if k >= 2 else "#1d2a44"}">{st}</text>')
            x += wd
        tot = sum(v for _, v in parts)
        s.append(f'<text x="{x + 14:.0f}" y="{y + 34}" class="tb">{tot / 1e6:.1f}M</text>'
                 f'<text x="1760" y="{y + 34}" class="tb" text-anchor="end">${pa[a]["cost_per_run"]:.2f}</text>')
        y += 90
    s.append(f'<text x="{x0}" y="{y - 20}" class="tsm">C, left to right: triage, spec (one run), implement '
             '(first build plus repairs), review.</text>')
    y += 20
    s.append(f'<text x="40" y="{y + 20}" class="t">Total for 32 runs: A ${pa["A"]["cost_total"]:.2f}, '
             f'B ${pa["B"]["cost_total"]:.2f}, C ${pa["C"]["cost_total"]:.2f}. Most input is cached (about 95%), '
             'so it is cheap per token.</text>')
    s.append(f'<text x="1760" y="{y + 70}" class="tsm" text-anchor="end">{SRC} (Codex session logs; '
             'results/main/analysis.json)</text>')
    return page(y + 100, "\n".join(s))


def stage_tokens():
    agg = collections.defaultdict(collections.Counter)
    for r in map(json.loads, open(MAIN / "bc-runs.jsonl")):
        d = MAIN / "runs" / r["ticket"] / r["arm"] / "codex" / str(r["rep"])
        ev = json.load(open(d / "evidence.json"))
        cmds = [x["command"] for x in json.load(open(d / "machinist-job.json"))["runs"]]
        assert len(cmds) == len(ev["sessions"]), d
        for c, s in zip(cmds, ev["sessions"]):
            t = s["tokens"] or {}
            agg[(r["arm"], c)]["input"] += t.get("input_tokens", 0)
            agg[(r["arm"], c)]["output"] += t.get("output_tokens", 0)
    return agg


def box(x, y, w, h, cls, lines, title=None, col=None):
    """A box with an optional coloured title bar and lines of text."""
    out = []
    if col:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#fff" stroke="{col}" stroke-width="4"/>'
                   f'<rect x="{x}" y="{y}" width="{w}" height="52" rx="14" fill="{col}"/>'
                   f'<rect x="{x}" y="{y + 36}" width="{w}" height="16" fill="{col}"/>'
                   f'<text x="{x + 20}" y="{y + 36}" class="tw" font-size="26">{title}</text>')
        y0 = y + 92
    else:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="{cls}"/>')
        if title:
            out.append(f'<text x="{x + 20}" y="{y + 40}" class="tb" font-size="27">{title}</text>')
        y0 = y + (82 if title else 44)
    for i, l in enumerate(lines):
        out.append(f'<text x="{x + 20}" y="{y0 + i * 34}" class="q">{l}</text>')
    return "".join(out)


def architecture():
    """How the trial was wired: arm A's rig, Machinist's control plane, worker, GitHub and the grader, plus one real
    job walked through (SUPPORTORDERS, C, run 4; quotes from its machinist-job.json)."""
    s = ['<text x="40" y="62" class="th">How the trial was wired</text>',
         '<text x="40" y="102" class="ts">Arm A on the left; Machinist (arms B and C) in the middle; one grader for '
         'all three. Every Codex session ran in its own bubblewrap sandbox.</text>']
    # arm A
    s.append(box(40, 140, 400, 300, None, ["Our rig (trialrig) starts", "one Codex 0.157 run:",
                                           "gpt-5.6-luna, medium effort", "Shopizer checkout, no GitHub",
                                           "Delivers: the changed files"], "A  one agent", COL["A"]))
    # Machinist
    s.append('<rect x="480" y="140" width="900" height="580" rx="18" fill="none" stroke="#1d2a44" '
             'stroke-width="3" stroke-dasharray="12 8"/>'
             '<text x="500" y="178" class="tb" font-size="27">Machinist (commit 4d7d776), on this machine</text>')
    s.append(box(500, 200, 420, 215, "box", ["Go foreman: checks each stage's", "reply, moves the job on",
                                             "SQLite jobs.db: jobs, attempts", "Jobs API on 127.0.0.1"],
                 "Control plane"))
    s.append(box(950, 200, 410, 215, "box", ["Starts a fresh Codex process", "per stage, in the project's",
                                             "own checkout, with GitHub", "token in the environment"],
                 "Local worker"))
    s.append('<path d="M920,305 L944,305" class="ln"/>')
    stages = [("Triage", "read-only", "brief"), ("Spec", "if triage asks", "auto-approved"),
              ("Implement", "commit, push", "open the PR"), ("Review", "read-only", "verdict")]
    x = 500
    for i, (n, a, b) in enumerate(stages):
        c = COL["C"] if n != "Implement" else COL["B"]
        s.append(f'<rect x="{x}" y="470" width="190" height="130" rx="12" fill="#fff" stroke="{c}" stroke-width="4"/>'
                 f'<text x="{x + 95}" y="512" class="tb" font-size="27" text-anchor="middle">{n}</text>'
                 f'<text x="{x + 95}" y="550" class="q" text-anchor="middle">{a}</text>'
                 f'<text x="{x + 95}" y="582" class="q" text-anchor="middle">{b}</text>')
        if i < 3:
            s.append(f'<path d="M{x + 190},535 L{x + 222},535" class="ln"/>')
        x += 225
    s.append('<path d="M1270,600 C1270,670 1045,670 1045,606" class="lnr"/>'
             '<text x="1125" y="694" class="q red" text-anchor="middle">changes asked: repair, up to 3 times</text>'
             '<path d="M1150,415 L1150,464" class="ln"/>')
    s.append('<text x="500" y="640" class="q">C runs all four stages.</text>'
             '<text x="500" y="672" class="q">B runs Implement only.</text>')
    # GitHub
    s.append(box(1420, 140, 340, 300, "boxt", ["One fresh private repo", "per run: asf-run-NNN", "(64 in the main run)",
                                               "Branch + pull request", "No CI checks (no arm had CI)"],
                 "GitHub App"))
    s.append('<path d="M1380,300 L1414,300" class="ln"/><path d="M1414,330 L1380,330" class="ln"/>')
    # grader
    s.append(box(1420, 500, 340, 220, "boxg", ["Hidden acceptance tests", "on A's files, or the PR head",
                                               "for B and C. No agent", "ever saw them."], "Grader (ours)"))
    s.append('<path d="M1590,440 L1590,494" class="ln"/>'
             '<path d="M240,440 L240,760 L1590,760 L1590,726" class="ln"/>')
    # one real job
    s.append('<rect x="40" y="800" width="1720" height="270" rx="14" class="box"/>'
             '<text x="70" y="846" class="tb" font-size="27">One real job, step by step (SUPPORTORDERS, arm C, run 4)</text>')
    steps = ["1. Triage: “Researched the order retention and pagination defects and prepared an implementation brief.”",
             "2. Implement: “Fixed deleted-customer order access and admin order pagination.” Pushed, PR opened.",
             "3. Review: “The diff is consistent with the requested behavior, but acceptance cannot be confirmed:",
             "    GitHub has zero check runs …”  Machinist ends the job: blocked.",
             "4. Our hidden tests on the same PR head: 12 of 12 pass."]
    for i, l in enumerate(steps):
        cls = "q green" if i == 4 else "q"
        s.append(f'<text x="70" y="{892 + i * 38}" class="{cls}" font-size="24">{l}</text>')
    s.append(f'<text x="1760" y="1110" class="tsm" text-anchor="end">{SRC} (README.md; Machinist ARCHITECTURE.md; '
             'results/main/runs/SUPPORTORDERS/C/codex/4/machinist-job.json)</text>')
    return page(1130, "\n".join(s))


def main():
    an = json.load(open(MAIN / "analysis.json"))
    re_ = json.load(open(MAIN / "review-effect.json"))
    st = stage_tokens()
    OUT.mkdir(exist_ok=True)
    for name, html in (("1-setup", setup()), ("2-scores", scores(an)), ("3-pipeline", pipeline(an, re_)),
                       ("4-tokens", tokens(an, st)), ("0-architecture", architecture())):
        (OUT / f"{name}.html").write_text(html)
        print(OUT / f"{name}.html")


if __name__ == "__main__":
    main()
