"""Writes the report's diagrams (diagrams/*.html, SVG 1800 px wide) from results/main. Render to PNG with diagrams/render.sh.
Colours: factory #1170a0 (blue), plain #d0731f (orange, also a different mark shape), neutral #b9b2a0.
Usage: python3 -I scripts/diagrams.py"""
import json, statistics as S
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "results/main"
OUT = ROOT / "diagrams"
FAC, PLN, OTH = "#1170a0", "#d0731f", "#b9b2a0"
SRC = "Source: github.com/meabs/experiments, 2026-11-design-factory"
A = json.loads((MAIN / "analysis.json").read_text())


def page(h, body):
    return (f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{h}" viewBox="0 0 1800 {h}">'
            '<defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1d2a44"/></marker></defs>'
            f'{body}<text x="40" y="{h - 22}" class="tsm">{SRC}</text></svg>\n')


def box(x, y, w, h, title, lines=(), cls="box"):
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" class="{cls}"/>', f'<text x="{x + 20}" y="{y + 38}" class="tb">{title}</text>']
    for i, l in enumerate(lines):
        s.append(f'<text x="{x + 20}" y="{y + 76 + i * 34}" class="t">{l}</text>')
    return "".join(s)


def setup():
    s = ['<text x="40" y="62" class="th">Same agent, same brief, same web search. One has the factory, one has nothing.</text>',
         '<text x="40" y="102" class="ts">Codex with gpt-5.6-luna at medium effort, six banking briefs, 5 repeats each: 60 runs, 30 pairs. Both are told to research, then storyboard.</text>',
         box(40, 150, 520, 360, "A  Plain agent", ["The workspace holds only", "a README.", "", "It gets the brief, the delivery", "contract and live web search,", "and uses its own knowledge."], "box"),
         box(620, 150, 1140, 360, "B  Design Factory", [], "boxt")]
    items = [("AGENTS.md", "points to the index"), ("okf/index.md", "lists everything below"), ("okf/workflow.md", "six stages, review mandatory"),
             ("12 skills", "research, storyboard, build, critique,"), ("", "accessibility, legal, banking, Impeccable"),
             ("rules and knowledge", "house rules, design, accessibility, UK law"), ("banking pack", "payments, savings, borrowing, cards"),
             ("tools", "contrast, lint, headless render check")]
    for i, (a, b) in enumerate(items):
        col, row = divmod(i, 4)
        x, y = 650 + col * 560, 215 + row * 70
        if a:
            s.append(f'<text x="{x}" y="{y + 24}" class="tb">{a}</text>')
        s.append(f'<text x="{x}" y="{y + (24 if not a else 52)}" class="t">{b}</text>')
    s += ['<text x="40" y="570" class="tb">Both arms deliver the same three things</text>',
          '<text x="40" y="612" class="t">research.md ending in numbered design decisions · storyboard/index.html with every screen addressable · storyboard/screens.json</text>',
          '<text x="40" y="680" class="tb">Judged blind, side by side, on screenshots</text>',
          '<text x="40" y="722" class="t">Two vision models from other providers, both orders, two views (first six screens; whole design), seven criteria.</text>',
          '<text x="40" y="768" class="t">Also measured without a model: brief checklist (12 items), axe-core accessibility violations, target sizes, cost.</text>',
          '<text x="40" y="814" class="t">Plain run i is paired with factory run i of the same brief; tests are sign-flip permutation tests on the 30 pairs.</text>']
    (OUT / "setup.html").write_text(page(880, "".join(s)))


def axis(x0, x1, y, h):
    s = []
    for v in (0, .25, .5, .75, 1):
        x = x0 + v * (x1 - x0)
        s.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + h}" stroke="{"#1d2a44" if v == .5 else "#ddd7c8"}" stroke-width="{3 if v == .5 else 2}"/>'
                 f'<text x="{x}" y="{y + h + 34}" class="tsm" text-anchor="middle">{v:.2f}</text>')
    return "".join(s)


def results():
    X0, X1 = 520, 1700
    px = lambda v: X0 + v * (X1 - X0)
    s = ['<text x="40" y="62" class="th">Judges: no clear whole-design preference, plain ahead on looks</text>',
         '<text x="40" y="102" class="ts">Share of judge votes for the factory design, per pair, averaged over 30 pairs (0.5 = no preference). Bar = 95% interval.</text>',
         f'<text x="{px(.1)}" y="150" class="tsm" text-anchor="middle">plain better</text><text x="{px(.9)}" y="150" class="tsm" text-anchor="middle">factory better</text>',
         axis(X0, X1, 164, 330)]
    rows = [("Whole design, original", .525, .392, .658), ("Whole design, cropped", .383, .25, .53),
            ("Looks only, original", .317, .19, .45), ("Looks only, cropped", .317, .21, .43)]
    for i, (n, m, lo, hi) in enumerate(rows):
        y = 205 + i * 78
        s.append(f'<text x="40" y="{y + 10}" class="t">{n}</text><line x1="{px(lo)}" y1="{y}" x2="{px(hi)}" y2="{y}" stroke="{FAC if m > .5 else PLN}" stroke-width="10" stroke-linecap="round"/>'
                 f'<circle cx="{px(m)}" cy="{y}" r="15" fill="#fff" stroke="#1d2a44" stroke-width="5"/><text x="{(px(lo) - 24) if m < .5 else (px(hi) + 24)}" y="{y + 10}" class="tb" text-anchor="{'end' if m < .5 else 'start'}">{m:.2f}</text>')
    s.append('<text x="40" y="560" class="th">What the judges rewarded, cropped screens</text>')
    s.append(f'<text x="40" y="600" class="ts">Mean pair score by criterion. Blue dot: whole design. Orange square: looks only (first six screens). Above 0.5 favours the factory.</text>')
    s.append(axis(X0, X1, 624, 250))
    crit = [("Identity", .12, .15), ("Polish", .24, .27), ("Hierarchy", .25, .30), ("Trust", .57, .50), ("Content", .62, .51), ("Journey", .65, None)]
    for i, (n, w, lk) in enumerate(crit):
        y = 655 + i * 38
        s.append(f'<text x="40" y="{y + 8}" class="t">{n}</text><circle cx="{px(w)}" cy="{y}" r="12" fill="{FAC}"/>')
        if lk is not None:
            s.append(f'<rect x="{px(lk) - 11}" y="{y - 11}" width="22" height="22" fill="{PLN}"/>')
    (OUT / "results.html").write_text(page(960, "".join(s)))


def checking():
    s = ['<text x="40" y="62" class="th">Checklist and accessibility favour the factory; research applied favours plain</text>',
         '<text x="40" y="102" class="ts">Means over 30 runs per arm. Higher is better except for axe violations. The last bar comes from a judge model; the others are counted.</text>']
    def bars(y, title, a, b, mx, fmt):
        out = [f'<text x="40" y="{y}" class="tb">{title}</text>']
        for i, (lab, v, c) in enumerate((("Plain", a, PLN), ("Factory", b, FAC))):
            yy = y + 24 + i * 62
            w = 900 * v / mx
            out.append(f'<text x="40" y="{yy + 38}" class="t">{lab}</text><rect x="260" y="{yy}" width="{max(w, 4)}" height="48" rx="6" fill="{c}"/>'
                       f'<text x="{260 + max(w, 4) + 18}" y="{yy + 36}" class="tb">{fmt(v)}</text>')
        return "".join(out)
    s.append(bars(170, "Brief checklist: items present out of 12 (key/states.json)", 0.59, 0.85, 1.0, lambda v: f"{v * 12:.1f} of 12"))
    s.append(bars(360, "axe-core violations per screen (WCAG 2.x A and AA)", 1.00, 0.06, 1.0, lambda v: f"{v:.2f}"))
    s.append(bars(550, "Controls at least 44 px in both directions", 0.51, 0.92, 1.0, lambda v: f"{v:.0%}"))
    s.append(bars(740, "Research decisions visibly applied (judge model)", 0.81, 0.68, 1.0, lambda v: f"{v:.0%}"))
    (OUT / "checking.html").write_text(page(960, "".join(s)))


def tokens():
    runs = A["runs"]
    X0, X1 = 330, 1700
    tot = lambda r: r["tokens"]["total"] / 1000
    mx = 2600
    px = lambda v: X0 + v / mx * (X1 - X0)
    s = ['<text x="40" y="62" class="th">The factory used about seven times the input tokens per run</text>',
         '<text x="40" y="102" class="ts">Total tokens (thousands) in each of the 60 runs; the tick is the mean for that brief and arm. Mean: plain 202k, factory 1,343k.</text>']
    for v in (0, 500, 1000, 1500, 2000, 2500):
        s.append(f'<line x1="{px(v)}" y1="140" x2="{px(v)}" y2="780" stroke="#ddd7c8" stroke-width="2"/><text x="{px(v)}" y="816" class="tsm" text-anchor="middle">{v:,}k</text>')
    for i, b in enumerate(["D1", "D2", "D3", "D4", "D5", "D6"]):
        y = 175 + i * 100
        s.append(f'<text x="40" y="{y + 40}" class="t">{b}</text>')
        for j, (arm, c) in enumerate((("A", PLN), ("B", FAC))):
            vals = [tot(r) for k, r in runs.items() if r["brief"] == b and r["arm"] == arm and r.get("tokens")]
            yy = y + 18 + j * 40
            for v in vals:
                s.append(f'<circle cx="{px(v)}" cy="{yy}" r="9" fill="{c}" fill-opacity=".75"/>' if arm == "B" else f'<rect x="{px(v) - 8}" y="{yy - 8}" width="16" height="16" fill="{c}" fill-opacity=".75"/>')
            m = S.mean(vals)
            s.append(f'<line x1="{px(m)}" y1="{yy - 17}" x2="{px(m)}" y2="{yy + 17}" stroke="#1d2a44" stroke-width="5"/>')
    s.append(f'<rect x="1280" y="150" width="20" height="20" fill="{PLN}"/><text x="1310" y="168" class="q">plain</text><circle cx="1420" cy="160" r="10" fill="{FAC}"/><text x="1440" y="168" class="q">factory</text>')
    (OUT / "tokens.html").write_text(page(880, "".join(s)))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    setup(); results(); checking(); tokens()
