"""TRX diagrams (diagrams/*.html, SVG 1800 px wide); render to PNG with diagrams/render.sh. Reads results/main/runs.csv.
Colours: dataviz categorical slots in fixed order (blue #2a78d6, orange #eb6834, yellow #eda100); every segment carries its
count as text. Usage: python3 -I scripts/diagrams.py"""
import csv, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "diagrams"
SRC = "Source: github.com/meabs/experiments, 2026-11-release-transition"
C = {"safe": "#2a78d6", "unsafe": "#eb6834", "none": "#eda100"}
SEGS = [("safe", "safe delivery", C["safe"]), ("unsafe", "released, unsafe", C["unsafe"]), ("none", "not delivered", C["none"])]
ARM = {"A": "A  independent agents", "B": "B  told to coordinate", "C": "C  plus the gate"}


def page(h, body):
    return f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{h}" viewBox="0 0 1800 {h}">\n{body}</svg>\n'


def stacked(title, sub, rows, note, x0=520, w=1170):
    s = [f'<text x="40" y="62" class="th">{title}</text>', f'<text x="40" y="102" class="ts">{sub}</text>']
    lx = 40
    for k, name, col in SEGS:
        s.append(f'<rect x="{lx}" y="136" width="26" height="26" rx="5" fill="{col}"/><text x="{lx + 38}" y="158" class="t">{name}</text>')
        lx += 70 + 15 * len(name)
    y = 200
    for label, cnt in rows:
        tot = sum(cnt.get(k, 0) for k, _, _ in SEGS)
        s.append(f'<text x="40" y="{y + 36}" class="tb">{label}</text><text x="40" y="{y + 64}" class="tsm">{tot} trajectories</text>')
        x = x0
        for k, name, col in SEGS:
            n = cnt.get(k, 0)
            if not n:
                continue
            wd = w * n / tot
            s.append(f'<rect x="{x + 1:.1f}" y="{y}" width="{max(wd - 2, 1):.1f}" height="68" rx="6" fill="{col}"/>')
            if wd > 40:
                s.append(f'<text x="{x + wd / 2:.1f}" y="{y + 45}" text-anchor="middle" class="tw" style="fill:#0b0b0b">{n}</text>')
            x += wd
        y += 92
    s.append(f'<text x="40" y="{y + 20}" class="ts">{note}</text>')
    s.append(f'<text x="1760" y="{y + 70}" class="tsm" text-anchor="end">{SRC} (results/main/runs.csv)</text>')
    return page(y + 90, "\n".join(s))


def outcome(r):
    if r["safe"] == "True":
        return "safe"
    return "unsafe" if r["released"] == "True" and r["delivered"] == "True" or r["n_violations"] not in ("", "0") else "none"


def main():
    R = list(csv.DictReader(open(ROOT / "results/main/runs.csv")))
    haz = [r for r in R if r["scenario"] != "S0"]
    rows = []
    for a in "ABC":
        c = collections.Counter(outcome(r) for r in haz if r["arm"] == a)
        rows.append((ARM[a], c))
    (OUT / "1-outcomes.html").write_text(stacked(
        "Told to coordinate, agents shipped safely 4 times in 5; left alone, 0 in 25",
        "Five hazard scenarios x 5 repetitions per arm. Every unsafe release in arm A passed its own CI first.",
        rows, "Safe delivery = released, requirements work, no oracle violation, rollback recovered."))
    names = {"S0": "S0  control", "S1": "S1  event schema", "S2": "S2  DB migration", "S3": "S3  retries", "S4": "S4  consent", "S5": "S5  decision model"}
    rows = []
    for s, n in names.items():
        for a in "ABC":
            c = collections.Counter(outcome(r) for r in R if r["scenario"] == s and r["arm"] == a)
            rows.append((f"{n}  {a}", c))
    (OUT / "2-by-scenario.html").write_text(stacked(
        "Consent (S4) is where coordination and the gate both fall short",
        "Per scenario and arm, 5 trajectories each. S0 is the control with no hazard.",
        rows, "Arm A = independent, B = told to coordinate, C = gate as well."))


main()
