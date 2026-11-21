"""Writes diagrams/chart-society.html (SVG, 1800 px wide) from results/main/world.sqlite3 (read-only)."""
import json, os, sqlite3, collections
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
db = sqlite3.connect(f"file:{os.path.join(root,'results','main','world.sqlite3')}?mode=ro", uri=True)
ev = [json.loads(p) for (p,) in db.execute("select payload from events order by id")]
last = db.execute("select max(day) from snapshots").fetchone()[0]
world = json.loads(db.execute("select payload from snapshots where day=?", (last,)).fetchone()[0])
WIN = 50; NW = 5
cnt = collections.defaultdict(collections.Counter)
for e in ev:
    cnt[(e["day"] - 1) // WIN][e["kind"]] += 1
panels = [("Contributions to public buildings", "contribute", "#2a78d6"), ("Completed trades", "trade", "#eb6834"),
          ("Chat messages", "message", "#1baf7a")]
W, H = 1800, 1000
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter,sans-serif"><rect width="{W}" height="{H}" fill="#fff"/>',
     '<text x="60" y="56" font-size="34" font-weight="700" fill="#1b2330">Everyone survived, then the town went quiet and a few residents piled up food</text>',
     f'<text x="60" y="92" font-size="20" fill="#667085">Two towns of eight residents, rules v2.1, stopped by the owner during day {last+1} (last complete day {last}). The last bar covers days 201 to {last}. Events are counted from the verified ledger.</text>']
PW, PH, y0 = 440, 260, 200
for i, (title, kind, col) in enumerate(panels):
    x0 = 100 + i * 580
    vals = [cnt[w][kind] for w in range(NW)]; hi = -(-max(vals) // 4) * 4 or 4
    s.append(f'<text x="{x0}" y="{y0-34}" font-size="22" font-weight="600" fill="#1b2330">{title}</text>')
    for k in range(5):
        v = hi * k / 4; y = y0 + PH - PH * k / 4
        s.append(f'<line x1="{x0}" x2="{x0+PW}" y1="{y}" y2="{y}" stroke="#e3e6ec"/><text x="{x0-10}" y="{y+6}" text-anchor="end" font-size="16" fill="#667085">{v:.0f}</text>')
    bw = PW / NW * 0.62
    for w, v in enumerate(vals):
        bx = x0 + w * PW / NW + (PW / NW - bw) / 2; bh = PH * v / hi
        s.append(f'<rect x="{bx}" y="{y0+PH-bh}" width="{bw}" height="{bh}" fill="{col}"/><text x="{bx+bw/2}" y="{y0+PH-bh-8}" text-anchor="middle" font-size="17" font-weight="600" fill="#1b2330">{v}</text>')
        lab = f"{w*WIN+1}-{(w+1)*WIN if w < NW-1 else last}"
        s.append(f'<text x="{bx+bw/2}" y="{y0+PH+26}" text-anchor="middle" font-size="15" fill="#667085">{lab}</text>')
    s.append(f'<text x="{x0+PW/2}" y="{y0+PH+52}" text-anchor="middle" font-size="16" fill="#667085">days</text>')
y1 = 640; PH2 = 250
s.append(f'<text x="100" y="{y1-60}" font-size="22" font-weight="600" fill="#1b2330">Food held by each resident after day {last} (both farmers hold most of it)</text>')
hi = -(-max(a["inventory"]["food"] for t in world["towns"].values() for a in t["agents"].values()) // 400) * 400
for k in range(5):
    v = hi * k / 4; y = y1 + PH2 - PH2 * k / 4
    s.append(f'<line x1="100" x2="1720" y1="{y}" y2="{y}" stroke="#e3e6ec"/><text x="90" y="{y+6}" text-anchor="end" font-size="16" fill="#667085">{v:.0f}</text>')
cols = {"Brook": "#2a78d6", "Flint": "#eb6834"}; slot = 1620 / 16; n = 0
for t, v in world["towns"].items():
    for name, a in v["agents"].items():
        f = a["inventory"]["food"]; bw = slot * 0.6; bx = 100 + n * slot + (slot - bw) / 2; bh = PH2 * f / hi
        s.append(f'<rect x="{bx}" y="{y1+PH2-bh}" width="{bw}" height="{bh}" fill="{cols[t]}"/><text x="{bx+bw/2}" y="{y1+PH2-bh-8}" text-anchor="middle" font-size="15" font-weight="600" fill="#1b2330">{f}</text>')
        s.append(f'<text x="{bx+bw/2}" y="{y1+PH2+24}" text-anchor="middle" font-size="15" fill="#667085">{name}</text><text x="{bx+bw/2}" y="{y1+PH2+42}" text-anchor="middle" font-size="13" fill="#667085">{a["role"]}</text>')
        n += 1
s.append(f'<text x="100" y="{y1+PH2+80}" font-size="18" fill="#1b2330"><tspan fill="#2a78d6" font-weight="700">&#9632;</tspan> Brook   <tspan fill="#eb6834" font-weight="700">&#9632;</tspan> Flint</text>')
s.append("</svg>")
os.makedirs(os.path.join(root, "diagrams"), exist_ok=True)
open(os.path.join(root, "diagrams", "chart-society.html"), "w").write('<!doctype html><meta charset="utf-8"><style>body{margin:0}</style>' + "".join(s))
