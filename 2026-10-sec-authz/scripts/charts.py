"""Draws the chart used on the website write-up, from the exported results.

Usage: uv run --with matplotlib python3 -I scripts/charts.py results [Inter font dir]   (reads results/main and
results/s05fix, writes results/chart-sec-authz.png)
Style follows the Programming the Loop guide charts (and okf-local's charts.py): 1800 x 920 px, Inter, beige / teal.
Left: secure functional completion of 80 runs per arm, as pre-registered and with the S05 rerun (higher is better).
Right: S03 runs where an approver could decide their own closure request, of 10 per arm (lower is better).
"""
import os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse  # noqa: E402

OUT = sys.argv[1]
if len(sys.argv) > 2:
    for f in os.listdir(sys.argv[2]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[2], f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID, MID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#6f9aa8"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-sec-authz/results (Codex 0.157, gpt-5.6-luna, medium effort). "
          "8 tasks × 10 runs per arm; corrected: S05 rerun for C and D with a fixed gate test.")
ARMS = [("A", "A: no help"), ("B", "B: security skill"), ("C", "C: security gate"), ("D", "D: skill + gate")]

runs = analyse.load(os.path.join(os.path.dirname(HERE), "results", "main"))
fix = [r for r in analyse.load(os.path.join(os.path.dirname(HERE), "results", "s05fix"))
       if r["task"] == "S05" and r["arm"] in ("C", "D")]
cor = [r for r in runs if not (r["task"] == "S05" and r["arm"] in ("C", "D"))] + fix
pre = {a: sum(r["pass"] for r in runs if r["arm"] == a) for a, _ in ARMS}
corr = {a: sum(r["pass"] for r in cor if r["arm"] == a) for a, _ in ARMS}
s03 = {a: sum("workflow (four-eyes)" in r["categories"] for r in runs if r["arm"] == a and r["task"] == "S03")
       for a, _ in ARMS}

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("Neither a skill nor a gate made the agent reliably secure; none fixed self-approval",
             x=0.01, ha="left", fontsize=13, y=0.96)
a1 = fig.add_axes([0.17, 0.16, 0.44, 0.62]); a2 = fig.add_axes([0.69, 0.16, 0.25, 0.62])
ys = [3, 2, 1, 0]
h = 0.36
for y, (a, _) in zip(ys, ARMS):
    a1.barh(y + h / 2, pre[a], height=h, color=BEIGE)
    a1.barh(y - h / 2, corr[a], height=h, color=TEAL)
    a1.text(pre[a] + 0.8, y + h / 2, f"{pre[a]}/80 as pre-registered", va="center", fontsize=8, color=NAVY)
    a1.text(corr[a] + 0.8, y - h / 2, f"{corr[a]}/80 corrected", va="center", fontsize=8, color=NAVY)
    a2.barh(y, s03[a], height=0.55, color=MID)
    a2.text(s03[a] + 0.3, y, f"{s03[a]}/10", va="center", fontsize=8.5, color=NAVY)
a1.set_xlim(0, 110); a1.set_xticks([0, 20, 40, 60, 80], ["0", "20", "40", "60", "80"], fontsize=9)
a1.set_title("Runs that worked and were secure, of 80 (higher is better)", fontsize=10, loc="left")
a2.set_xlim(0, 13); a2.set_xticks([0, 5, 10], ["0", "5", "10"], fontsize=9)
a2.set_title("S03: an approver could decide their\nown request, of 10 (lower is better)", fontsize=10, loc="left")
a1.set_yticks(ys, [a[1] for a in ARMS], fontsize=9)
a2.set_yticks(ys, [""] * 4)
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.03, SOURCE, fontsize=7, color=MUTED)
p = os.path.join(OUT, "chart-sec-authz.png")
fig.savefig(p, facecolor="white")
print(p, pre, corr, s03)
