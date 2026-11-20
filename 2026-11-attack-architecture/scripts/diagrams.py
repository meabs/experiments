"""Writes diagrams/chart-curves.html (SVG, 1800 px wide) from results/main*/ games, and the two real-game viewers."""
import json, glob, os, statistics as st
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MODELS = [("main", "qwen3.8:27b"), ("main-huihui", "Qwen3.8-abliterated")]
ARMS = [("N", "No defender", "#2a78d6"), ("F", "Free redesign", "#eb6834"), ("S", "Subtractive", "#1baf7a"), ("M", "Minimal fix", "#e87ba4")]
def curves(d):
    out = {}
    for arm, _, _ in ARMS:
        gs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(root, "results", d, f"*-{arm}-*.json")))]
        for key in ("paths", "complexity"):
            ser = []
            for g in gs:
                v = [g["start"][key]] + [r["ma"][key] for r in g["rounds"]]
                v += [v[-1]] * (9 - len(v)); ser.append(v)
            out[(arm, key)] = [st.mean(s[i] for s in ser) for i in range(9)]
    return out
W, H = 1800, 1080; PW, PH = 540, 300
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter,sans-serif"><rect width="{W}" height="{H}" fill="#fff"/>',
       '<text x="60" y="56" font-size="34" font-weight="700" fill="#1b2330">Every defender closed most attack paths; only the subtractive one made the system smaller</text>',
       '<text x="60" y="92" font-size="20" fill="#667085">Mean over 12 games per arm (4 systems x 3 repetitions). A stopped game keeps its last value. Round 0 is the starting system.</text>']
for mi, (d, name) in enumerate(MODELS):
    c = curves(d)
    for ki, (key, title, lo, hi) in enumerate([("paths", "Open attack paths", 0, 3), ("complexity", "Complexity (parts and wiring)", 33, 38)]):
        x0 = 100 + ki * 880; y0 = 200 + mi * 450
        svg.append(f'<text x="{x0}" y="{y0-34}" font-size="22" font-weight="600" fill="#1b2330">{name}: {title}</text>')
        X = lambda i: x0 + i * PW / 8; Y = lambda v: y0 + PH - (v - lo) / (hi - lo) * PH
        for k in range(hi - lo + 1):
            v = lo + k
            svg.append(f'<line x1="{x0}" x2="{x0+PW}" y1="{Y(v)}" y2="{Y(v)}" stroke="#e3e6ec"/><text x="{x0-10}" y="{Y(v)+6}" text-anchor="end" font-size="16" fill="#667085">{v:.0f}</text>')
        for i in range(9): svg.append(f'<text x="{X(i)}" y="{y0+PH+28}" text-anchor="middle" font-size="16" fill="#667085">{i}</text>')
        svg.append(f'<text x="{x0+PW/2}" y="{y0+PH+54}" text-anchor="middle" font-size="16" fill="#667085">round</text>')
        ends = []
        for arm, label, col in ARMS:
            v = c[(arm, key)]; svg.append(f'<polyline fill="none" stroke="{col}" stroke-width="4" points="' + " ".join(f"{X(i)},{Y(max(lo,min(hi,x)))}" for i, x in enumerate(v)) + '"/>')
            for i, x in enumerate(v): svg.append(f'<circle cx="{X(i)}" cy="{Y(max(lo,min(hi,x)))}" r="4.5" fill="{col}"/>')
            ends.append((Y(max(lo, min(hi, v[-1]))), label, col, v[-1]))
        ends.sort(); last = -99
        for y, label, col, val in ends:
            y = max(y, last + 22); last = y
            svg.append(f'<text x="{x0+PW+12}" y="{y+6}" font-size="18" fill="#1b2330"><tspan fill="{col}" font-weight="700">&#9632;</tspan> {label} {val:.1f}</text>')
svg.append('</svg>')
os.makedirs(os.path.join(root, "diagrams"), exist_ok=True)
open(os.path.join(root, "diagrams", "chart-curves.html"), "w").write('<!doctype html><meta charset="utf-8"><body style="margin:0">' + "".join(svg))
for d, name in MODELS:
    games = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(root, "results", d, "*-*-*.json")))]
    for g in games: g["demo"] = False; g["calls"] = []
    p = os.path.join(root, "results", d, "games-viewer.json"); json.dump(games, open(p, "w"))
    os.system(f'python3 -I {os.path.join(root, "scripts", "build_viewer.py")} {p} {os.path.join(root, "diagrams", "observer-" + d + ".html")}')
