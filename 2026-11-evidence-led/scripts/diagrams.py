"""Writes the report's diagrams (diagrams/*.html, SVG at 1800 px wide) from results/main. Render them to PNG with
diagrams/render.sh.

Colours, in the fixed order V, D, E (dataviz palette validator, light mode: lightness, chroma, colour-blind
separation, normal-vision floor and contrast all pass): V #6f8f2f, D #1170a0, E #d0731f. Every bar is also labelled
with its arm, so identity never rests on colour alone.

Usage: python3 -I scripts/diagrams.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "results/main"
OUT = ROOT / "diagrams"
ARMS = [("V", "V  vanilla"), ("D", "D  disciplined"), ("E", "E  evidence-led")]
COL = {"V": "#6f8f2f", "D": "#1170a0", "E": "#d0731f"}
SRC = "Source: github.com/meabs/experiments, 2026-11-evidence-led"


def page(h, body):
    return (f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{h}" viewBox="0 0 1800 {h}">'
            f'\n{body}</svg>\n')


def setup():
    cols = [
        ("V", "V  vanilla", ["Shopizer as it is", "Codex defaults", "(sub-agents on, hooks on)", "", "", ""]),
        ("D", "D  disciplined", ["AGENTS.md: 6 general lines", "3 small skills:", "  requirements-check",
                                 "  build-and-verify", "  self-review", ""]),
        ("E", "E  evidence-led v1", ["AGENTS.md: 3 lines from findings", "  (mvn -o test, count tests,",
                                     "  follow the code)", "user AGENTS.md: injection rule", "sub-agents off",
                                     "stop gate: build + 40 tests"]),
    ]
    s = ['<text x="40" y="62" class="th">Three setups, six hard bug reports, five runs each</text>',
         '<text x="40" y="102" class="ts">Same agent (Codex, gpt-5.6-luna, medium effort) and the same Shopizer '
         'commit in every arm; only what the agent is given differs.</text>']
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
             '<text x="70" y="600" class="t">• Tickets: real Shopizer defects with hidden, interacting causes, written '
             'as a merchant\'s bug report. Nothing planted.</text>'
             '<text x="70" y="650" class="t">• Score: the share of hidden acceptance tests passed (9 to 15 a ticket), '
             'graded after the run; the agent never sees them.</text>')
    s.append(f'<text x="1760" y="740" class="tsm" text-anchor="end">{SRC} (README.md, arms/)</text>')
    return page(770, "\n".join(s))


def scores(an):
    pt, tickets = an["per_ticket"], an["tickets"]
    x0, w = 420, 1150
    s = ['<text x="40" y="62" class="th">The disciplined setup scored highest; on two tickets nothing helped</text>',
         '<text x="40" y="102" class="ts">Mean share of hidden tests passed, 5 runs per arm and ticket (higher is '
         'better). Dots: single runs (equal scores overlap). Right: the mean.</text>']
    y = 150
    order = ["PRODUCTDELETE", "SUPPORTORDERS", "STOCK", "REVIEWS", "CATEGORYDELETE", "CUSTOMERCART"]
    order = [t for t in order if t in tickets] + [t for t in tickets if t not in order]
    for t in order:
        s.append(f'<text x="40" y="{y + 26}" class="tb">{t}</text>')
        y += 44
        for a, label in ARMS:
            m = pt[t][a]["mean"]
            s.append(f'<text x="{x0 - 20}" y="{y + 24}" class="q" text-anchor="end">{label}</text>'
                     f'<rect x="{x0}" y="{y + 4}" width="{max(4, m * w):.0f}" height="28" rx="4" fill="{COL[a]}"/>'
                     f'<text x="1700" y="{y + 27}" class="q" font-weight="650" text-anchor="end">{m * 100:.0f}%</text>')
            for v in pt[t][a]["scores"]:
                s.append(f'<circle cx="{x0 + v * w:.0f}" cy="{y + 18}" r="6" fill="#fff" stroke="#1d2a44" '
                         'stroke-width="2.5"/>')
            y += 38
        y += 22
    for k in range(0, 101, 25):
        x = x0 + k / 100 * w
        s.append(f'<line x1="{x:.0f}" y1="140" x2="{x:.0f}" y2="{y - 10}" stroke="#d9d3c4" stroke-width="1.5"/>'
                 f'<text x="{x:.0f}" y="{y + 18}" class="tsm" text-anchor="middle">{k}%</text>')
    y += 50
    pa = an["per_arm"]
    s.append(f'<rect x="40" y="{y}" width="1720" height="150" rx="14" class="box"/>'
             f'<text x="70" y="{y + 50}" class="t">• Over all six (each ticket counts equally): V {pa["V"]["mean_score"] * 100:.0f}%, '
             f'D {pa["D"]["mean_score"] * 100:.0f}%, E {pa["E"]["mean_score"] * 100:.0f}%.</text>'
             f'<text x="70" y="{y + 100}" class="t">• Only D beat V after Holm correction; E vs D: no measurable '
             'difference, E slightly lower.</text>')
    s.append(f'<text x="1760" y="{y + 190}" class="tsm" text-anchor="end">{SRC} (results/main/analysis.json)</text>')
    return page(y + 220, "\n".join(s))


def mechanisms(mech):
    items = [("wrote a test", "wrote a new test"), ("ran full suite", "ran the whole existing suite"),
             ("false_claims", "said done and passing, hidden tests failed")]
    x0, w = 620, 1000
    s = ['<text x="40" y="62" class="th">What the setups changed: D\'s agents wrote tests; E\'s ran the suite</text>',
         '<text x="40" y="102" class="ts">Runs out of 30 per arm. Writing and running tests: from the agents\' commands '
         'and diffs; false claims: README section 5 rule.</text>']
    y = 150
    for k, name in items:
        s.append(f'<text x="40" y="{y + 26}" class="tb">{name}</text>')
        y += 44
        for a, label in ARMS:
            v = mech[a][k]
            s.append(f'<text x="{x0 - 20}" y="{y + 24}" class="q" text-anchor="end">{label}</text>'
                     f'<rect x="{x0}" y="{y + 4}" width="{max(4, v / 30 * w):.0f}" height="28" rx="4" fill="{COL[a]}"/>'
                     f'<text x="{x0 + v / 30 * w + 12:.0f}" y="{y + 27}" class="q" font-weight="650">{v}</text>')
            y += 38
        y += 22
    y += 20
    s.append(f'<rect x="40" y="{y}" width="1720" height="150" rx="14" class="box"/>'
             f'<text x="70" y="{y + 50}" class="t">• Every D run opened all three skills; D\'s AGENTS.md says to add or '
             'update tests. E\'s gate never had to block.</text>'
             f'<text x="70" y="{y + 100}" class="t">• Whatever the setup, a run that missed hidden tests almost always '
             'reported success.</text>')
    s.append(f'<text x="1760" y="{y + 190}" class="tsm" text-anchor="end">{SRC} (results/main/mechanisms.json)</text>')
    return page(y + 220, "\n".join(s))


def tokens(an):
    pa = an["per_arm"]
    scale = 1000 / 3_500_000
    x0 = 400
    s = ['<text x="40" y="62" class="th">Tokens per run: D read the most, as it also wrote and ran tests</text>',
         '<text x="40" y="102" class="ts">Mean tokens per run (lower is cheaper). Bar: input tokens, cached (light) '
         'and new (dark). Right column: output tokens.</text>',
         '<rect x="420" y="128" width="26" height="26" rx="4" fill="#c9c4b6"/><text x="456" y="150" class="q">'
         'cached input</text>'
         '<rect x="680" y="128" width="26" height="26" rx="4" fill="#4a5873"/><text x="716" y="150" class="q">'
         'new input</text><text x="1700" y="190" class="q" font-weight="650" text-anchor="end">output</text>']
    y = 210
    for a, label in ARMS:
        v = pa[a]["tokens"]
        c, n = v["cached"] * scale, (v["input"] - v["cached"]) * scale
        s.append(f'<rect x="{x0 - 300}" y="{y + 8}" width="20" height="20" rx="4" fill="{COL[a]}"/>'
                 f'<text x="{x0 - 20}" y="{y + 25}" class="q" text-anchor="end">{label}</text>'
                 f'<rect x="{x0}" y="{y + 4}" width="{c - 2:.0f}" height="28" fill="#c9c4b6"/>'
                 f'<rect x="{x0 + c:.0f}" y="{y + 4}" width="{n:.0f}" height="28" fill="#4a5873"/>'
                 f'<text x="{x0 + c + n + 10:.0f}" y="{y + 27}" class="q" font-weight="650">'
                 f'{v["input"] / 1e6:.2f}M</text>'
                 f'<text x="1700" y="{y + 27}" class="q" text-anchor="end">{v["output"] / 1000:.1f}k</text>')
        y += 48
    for k in range(0, 3_500_001, 1_000_000):
        x = x0 + k * scale
        s.append(f'<line x1="{x:.0f}" y1="200" x2="{x:.0f}" y2="{y}" stroke="#d9d3c4" stroke-width="1.5"/>'
                 f'<text x="{x:.0f}" y="{y + 28}" class="tsm" text-anchor="middle">{k / 1e6:.0f}M</text>')
    y += 70
    s.append(f'<rect x="40" y="{y}" width="1720" height="150" rx="14" class="box"/>'
             f'<text x="70" y="{y + 50}" class="t">• Cost per run at list price: V ${pa["V"]["cost_per_run"]:.3f}, '
             f'D ${pa["D"]["cost_per_run"]:.3f}, E ${pa["E"]["cost_per_run"]:.3f}; all 90 runs '
             f'${sum(p["cost"] for p in pa.values()):.2f}.</text>'
             f'<text x="70" y="{y + 100}" class="t">• Wall time per run: V {pa["V"]["seconds_mean"] / 60:.1f} min, '
             f'D {pa["D"]["seconds_mean"] / 60:.1f} min, E {pa["E"]["seconds_mean"] / 60:.1f} min.</text>')
    s.append(f'<text x="1760" y="{y + 190}" class="tsm" text-anchor="end">{SRC} (Codex token counts, gpt-5.6-luna '
             'list price)</text>')
    return page(y + 220, "\n".join(s))


def main():
    an = json.loads((MAIN / "analysis.json").read_text())
    mech = json.loads((MAIN / "mechanisms.json").read_text())["per_arm"]
    OUT.mkdir(exist_ok=True)
    for name, html in (("1-setup", setup()), ("2-scores", scores(an)), ("3-mechanisms", mechanisms(mech)),
                       ("4-tokens", tokens(an))):
        (OUT / f"{name}.html").write_text(html)
        print(OUT / f"{name}.html")


if __name__ == "__main__":
    main()
