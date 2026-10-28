"""Draws the chart used on the website write-up, from the exported results.

Usage: uv run --with matplotlib python3 -I scripts/charts.py results [Inter font dir]   (reads results/main, writes there)
Style follows the Programming the Loop guide charts (and split-spec's charts.py): 1800 x 920 px, Inter, beige / teal.
Left: changes that passed their hidden test, of 20, local and hosted (higher is better). Right: median wall time per
local run (lower is better).
"""
import os, statistics as st, sys

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
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-okf-local/results (Codex 0.157, qwen3.8:27b local, medium effort; "
          "hosted: OKF test G, gpt-5.6-luna). 4 tasks × 5 runs per arm.")
ARMS = [("no_okf", "No guide (backend not available)"), ("okf", "The backend's guide"), ("source", "The backend's source")]

runs = analyse.load(os.path.join(os.path.dirname(HERE), "results", "main"))
local = {a: sum(r["pass"] for r in runs if r["arm"] == a) for a, _ in ARMS}
hosted = {a: sum(analyse.HOSTED[a]) for a, _ in ARMS}
mins = {a: st.median(r["seconds"] for r in runs if r["arm"] == a) / 60 for a, _ in ARMS}

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("A small local model got nearly every change right with the backend's guide or its source",
             x=0.01, ha="left", fontsize=13, y=0.96)
a1 = fig.add_axes([0.27, 0.16, 0.40, 0.62]); a2 = fig.add_axes([0.74, 0.16, 0.22, 0.62])
ys = [2, 1, 0]
h = 0.34
for y, (a, _) in zip(ys, ARMS):
    a1.barh(y + h / 2, local[a], height=h, color=TEAL)
    a1.barh(y - h / 2, hosted[a], height=h, color=BEIGE)
    a1.text(local[a] + 0.3, y + h / 2, f"{local[a]}/20 local", va="center", fontsize=8, color=NAVY)
    a1.text(hosted[a] + 0.3, y - h / 2, f"{hosted[a]}/20 hosted", va="center", fontsize=8, color=NAVY)
    a2.barh(y, mins[a], height=0.55, color=MID)
    a2.text(mins[a] + 0.15, y, f"{mins[a]:.1f} min", va="center", fontsize=8.5, color=NAVY)
a1.set_xlim(0, 26); a1.set_xticks([0, 5, 10, 15, 20], ["0", "5", "10", "15", "20"], fontsize=9)
a1.set_title("Changes passing the hidden test, of 20 (higher is better)", fontsize=10, loc="left")
a2.set_xlim(0, 10); a2.set_xticks([0, 4, 8], ["0", "4", "8"], fontsize=9)
a2.set_title("Median minutes per local run\n(lower is better; hosted ≈ 0.7)", fontsize=10, loc="left")
a1.set_yticks(ys, [a[1] for a in ARMS], fontsize=9)
a2.set_yticks(ys, [""] * 3)
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.03, SOURCE, fontsize=7, color=MUTED)
p = os.path.join(OUT, "chart-okl-guide.png")
fig.savefig(p, facecolor="white")
print(p, local, hosted, {k: round(v, 1) for k, v in mins.items()})
