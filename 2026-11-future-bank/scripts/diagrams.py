"""Report diagrams (SVG 1800 px) from results/main: pair scores by criterion, tokens per run. Render: bash diagrams/render.sh.
Factory #1170a0 (circles), plain #d0731f (squares). Usage: python3 -I scripts/diagrams.py"""
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
MAIN, OUT = R / "results/main", R / "diagrams"
FAC, PLN = "#1170a0", "#d0731f"
SRC = "Source: github.com/meabs/experiments, 2026-11-future-bank"
A = json.loads((MAIN / "analysis.json").read_text()); AC = json.loads((MAIN / "analysis-crop.json").read_text())


def page(h, body):
    return (f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{h}" viewBox="0 0 1800 {h}">{body}'
            f'<text x="40" y="{h - 22}" class="tsm">{SRC}</text></svg>\n')


def results():
    names = [("overall", "Overall"), ("novelty", "Novelty"), ("fit", "Fit for a new generation"), ("plausible", "Plausible as a UK bank"),
             ("hierarchy", "Hierarchy"), ("polish", "Polish"), ("identity", "Identity")]
    x0, x1 = 520, 1640
    X = lambda v: x0 + (x1 - x0) * v
    s = ['<text x="40" y="62" class="th">Plain won every pair on novelty, fit and identity; the factory led on plausibility</text>',
         '<text x="40" y="102" class="ts">Share of judge votes for the factory design, mean over 25 pairs. 0.5 is no preference; left of the line favours plain, right favours the factory.</text>']
    for t in (0, .25, .5, .75, 1):
        s.append(f'<line x1="{X(t)}" y1="140" x2="{X(t)}" y2="770" stroke="{"#1d2a44" if t == .5 else "#ddd7c8"}" stroke-width="{3 if t == .5 else 2}"/>'
                 f'<text x="{X(t)}" y="806" class="tsm" text-anchor="middle">{t:g}</text>')
    for i, (k, n) in enumerate(names):
        y = 190 + i * 85
        s.append(f'<text x="40" y="{y + 8}" class="t">{n}</text>')
        a = A[k]
        s.append(f'<line x1="{X(a["lo"])}" y1="{y - 12}" x2="{X(a["hi"])}" y2="{y - 12}" stroke="#1d2a44" stroke-width="5"/>'
                 f'<circle cx="{X(a["mean"])}" cy="{y - 12}" r="11" fill="{FAC}"/>'
                 f'<text x="{X(a["mean"])}" y="{y - 34}" class="tsm" text-anchor="middle">{a["mean"]:.2f}</text>')
        c = AC[k]["mean"]
        s.append(f'<rect x="{X(c) - 9}" y="{y + 16}" width="18" height="18" fill="none" stroke="{FAC}" stroke-width="4"/>')
    s.append(f'<circle cx="1180" cy="846" r="9" fill="{FAC}"/><text x="1200" y="852" class="tsm">uncropped captures, with 95% interval (primary)</text>'
             f'<rect x="1171" y="868" width="18" height="18" fill="none" stroke="{FAC}" stroke-width="4"/><text x="1200" y="882" class="tsm">cropped re-score</text>')
    (OUT / "results.html").write_text(page(920, "".join(s)))


def tokens():
    x0, x1 = 330, 1700
    d = {}
    for a in "AB":
        d[a] = [json.load(open(f))["tokens"]["total"] / 1000 for f in sorted(MAIN.glob(f"{a}/runs/F1/{a}/codex/*/run.json"))]
    mx = 2500
    X = lambda v: x0 + (x1 - x0) * v / mx
    s = ['<text x="40" y="62" class="th">The factory used about five times the tokens per run</text>',
         f'<text x="40" y="102" class="ts">Total tokens (thousands) in each of the 10 runs; the tick is the mean. Mean: plain {sum(d["A"]) / 5:,.0f}k, factory {sum(d["B"]) / 5:,.0f}k.</text>']
    for t in range(0, 2501, 500):
        s.append(f'<line x1="{X(t)}" y1="140" x2="{X(t)}" y2="400" stroke="#ddd7c8" stroke-width="2"/><text x="{X(t)}" y="436" class="tsm" text-anchor="middle">{t:,}k</text>')
    for row, (a, name, col) in enumerate((("A", "Plain", PLN), ("B", "Factory", FAC))):
        y = 220 + row * 100
        s.append(f'<text x="40" y="{y + 8}" class="t">{name}</text>')
        for v in d[a]:
            s.append(f'<rect x="{X(v) - 8}" y="{y - 8}" width="16" height="16" fill="{col}" fill-opacity=".75"/>' if a == "A" else
                     f'<circle cx="{X(v)}" cy="{y}" r="9" fill="{col}" fill-opacity=".75"/>')
        m = sum(d[a]) / 5
        s.append(f'<line x1="{X(m)}" y1="{y - 28}" x2="{X(m)}" y2="{y + 28}" stroke="#1d2a44" stroke-width="5"/>')
    (OUT / "tokens.html").write_text(page(540, "".join(s)))


if __name__ == "__main__":
    results(); tokens()
