"""TRX-2 diagrams (diagrams/*.html, SVG 1800 px wide); render with diagrams/render.sh. Reads results/main/runs.csv.
Colours: dataviz categorical slots in fixed order (blue #2a78d6, aqua #1baf7a, orange #eb6834, yellow #eda100); every segment has its
count as text. Usage: python3 -I scripts/diagrams.py"""
import csv, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "diagrams"
SRC = "Source: github.com/meabs/experiments, 2026-11-mature-pipeline"
SEGS = [("first", "safe first time", "#2a78d6"), ("repaired", "safe after repair", "#1baf7a"),
        ("unsafe", "released, not safe", "#eb6834"), ("held", "held, not released", "#eda100")]
ARM = {"A": "A  independent agents", "B": "B  plus awareness", "C": "C  plus release plan"}


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
        return "first" if r["safe_first"] == "True" else "repaired"
    return "held" if r["released"] == "False" else "unsafe"


def main():
    R = list(csv.DictReader(open(ROOT / "results/main/runs.csv")))
    haz = [r for r in R if r["scenario"] != "S0"]
    rows = [(ARM[a], collections.Counter(outcome(r) for r in haz if r["arm"] == a)) for a in "ABC"]
    (OUT / "1-outcomes.html").write_text(stacked(
        "The pipeline got independent agents to 11 of 25 safe; awareness to 20, a release plan to 22", "Five hazard scenarios x 5 repetitions per arm; the same mature pipeline in every arm, up to two repair rounds.",
        rows, "Safe delivery = released, requirements work, no oracle violation, rollback recovered."))
    names = {"S0": "S0  control", "S1": "S1  event schema", "S2": "S2  DB migration", "S3": "S3  retries", "S4": "S4  consent", "S5": "S5  decision model"}
    rows = [(f"{n}  {a}", collections.Counter(outcome(r) for r in R if r["scenario"] == s and r["arm"] == a)) for s, n in names.items() for a in "ABC"]
    (OUT / "2-by-scenario.html").write_text(stacked("Retries (S3) and the decision model (S5) are where independent agents never converge", "Per scenario and arm, 5 trajectories each. S0 is the control with no hazard.",
                                                    rows, "Arm A = independent, B = plus awareness, C = plus awareness and release plan."))


main()
