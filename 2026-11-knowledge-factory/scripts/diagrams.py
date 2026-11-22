"""Writes diagrams/chart-kf.html (SVG, 1800 px wide) from results/main/analysis.json and runs.csv."""
import csv, json, os
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
rows = list(csv.DictReader(open(os.path.join(root, "results/main/runs.csv"))))
COL = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a", "D": "#eda100"}
NAME = {"A": "A static", "B": "B self-maintaining", "C": "C factory", "D": "D evidence gate"}
W, H = 1800, 900
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter,Arial,sans-serif"><rect width="{W}" height="{H}" fill="#fff"/>',
     '<text x="60" y="56" font-size="34" font-weight="700" fill="#1b2330">Stored knowledge helped the fresh agent; nobody stored the planted lie</text>',
     '<text x="60" y="92" font-size="20" fill="#667085">Four seeds per arm, five stages, qwen3.8:27b workers and curators. Scores are hidden-test pass rates; claims are graded by code.</text>']
# panel 1: stage-5 score per seed
x0, y0, PW, PH = 100, 220, 700, 460
s.append(f'<text x="{x0}" y="{y0-40}" font-size="22" font-weight="600" fill="#1b2330">Stage 5 score of a fresh agent on a new partner (one dot per seed)</text>')
for k in range(5):
    v = 0.5 + 0.5 * k / 4; y = y0 + PH - PH * (v - 0.5) / 0.5
    s.append(f'<line x1="{x0}" x2="{x0+PW}" y1="{y}" y2="{y}" stroke="#e3e6ec"/><text x="{x0-10}" y="{y+6}" text-anchor="end" font-size="16" fill="#667085">{v:.2f}</text>')
for i, a in enumerate("ABCD"):
    cx = x0 + 90 + i * 170
    sc = [float(r["score"]) for r in rows if r["arm"] == a and r["stage"] == "5"]
    mean = sum(sc) / len(sc)
    ym = y0 + PH - PH * (mean - 0.5) / 0.5
    s.append(f'<line x1="{cx-45}" x2="{cx+45}" y1="{ym}" y2="{ym}" stroke="{COL[a]}" stroke-width="4"/>')
    seen = {}
    for v in sc:
        n = seen.get(round(v, 3), 0); seen[round(v, 3)] = n + 1
        y = y0 + PH - PH * (v - 0.5) / 0.5
        s.append(f'<circle cx="{cx-30+n*20}" cy="{y}" r="9" fill="{COL[a]}" fill-opacity=".85"/>')
    s.append(f'<text x="{cx}" y="{y0+PH+34}" text-anchor="middle" font-size="18" fill="#1b2330">{NAME[a].split(" ",1)[0]}</text><text x="{cx}" y="{y0+PH+58}" text-anchor="middle" font-size="15" fill="#667085">{NAME[a].split(" ",1)[1]}</text>')
    s.append(f'<text x="{cx+52}" y="{ym+6}" font-size="16" fill="#1b2330">{mean:.2f}</text>')
# panel 2: claims in the store by stage
x1 = 960
s.append(f'<text x="{x1}" y="{y0-40}" font-size="22" font-weight="600" fill="#1b2330">Claims in the store after each stage (mean of four seeds)</text>')
hi = 12
for k in range(5):
    v = hi * k / 4; y = y0 + PH - PH * k / 4
    s.append(f'<line x1="{x1}" x2="{x1+PW}" y1="{y}" y2="{y}" stroke="#e3e6ec"/><text x="{x1-10}" y="{y+6}" text-anchor="end" font-size="16" fill="#667085">{v:.0f}</text>')
for st in range(1, 5):
    x = x1 + 60 + (st - 1) * 190
    s.append(f'<text x="{x}" y="{y0+PH+34}" text-anchor="middle" font-size="18" fill="#1b2330">Stage {st}</text>')
for a in "ABCD":
    pts = []
    for st in range(1, 5):
        v = [float(r["claims"]) for r in rows if r["arm"] == a and r["stage"] == str(st)]
        m = sum(v) / len(v)
        pts.append((x1 + 60 + (st - 1) * 190, y0 + PH - PH * m / hi, m))
    s.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y,_ in pts)}" fill="none" stroke="{COL[a]}" stroke-width="4"/>')
    for x, y, m in pts:
        s.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{COL[a]}"/>')
    s.append(f'<text x="{pts[-1][0]+14}" y="{pts[-1][1]+6}" font-size="16" fill="#1b2330">{a} {pts[-1][2]:.1f}</text>')
cont = sum(int(r["contamination"]) for r in rows if r["stage"] in ("4", "5"))
s.append(f'<text x="60" y="{H-60}" font-size="20" fill="#1b2330">Contaminated claims (planted lie or stale v1 fields) at stages 4 and 5, all arms and seeds: {cont}.</text>')
s.append(f'<text x="60" y="{H-28}" font-size="16" fill="#667085">Source: results/main/runs.csv. Arm A never changes its three starting claims. Y axis of the left panel starts at 0.50.</text></svg>')
open(os.path.join(root, "diagrams/chart-kf.html"), "w").write('<!doctype html><meta charset="utf-8"><body style="margin:0">' + "\n".join(s))
