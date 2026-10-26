"""Draws the chart used on the website write-up, from the exported results.

Usage: uv run --with matplotlib python3 -I scripts/charts.py <out dir> [font dir]
Style follows the Programming the Loop guide charts (and swarm-tax's charts.py): 1800 x 920 px, Inter,
beige / teal. Left: share of hidden tests passed, mean over the six tasks (higher is better). Right: mean cost per run
(lower is better).
"""
import os, statistics as st, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "2026-10-swarm-tax", "scripts"))
import analyse as base  # noqa: E402  (swarm-tax's loader, pointed at this experiment as split-spec's analyse.py does)
E = os.path.dirname(HERE)
base.E, base.HERE = E, HERE
by_task, load = base.by_task, base.load  # noqa: E402

OUT = sys.argv[1]
if len(sys.argv) > 2:
    for f in os.listdir(sys.argv[2]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[2], f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID, MID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#6f9aa8"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-split-spec/results "
          "(Codex 0.157, gpt-5.6-luna, medium effort; 6 features × 6 runs per setup).")
R = os.path.join(E, "results")
ARMS = [("solo", "One agent", os.path.join(R, "main", "solo")),
        ("team-spec", "Team, one coder (task file shared)", os.path.join(R, "main", "team-spec")),
        ("split-part", "Split: 3 coders, each sees its part only", os.path.join(R, "main", "split-part")),
        ("split-full", "Split: 3 coders, each sees the whole task", os.path.join(R, "main", "split-full"))]

score, cost = {}, {}
for arm, _, d in ARMS:
    rs = load([d])
    g = by_task(rs, arm)
    score[arm] = 100 * st.mean(st.mean(r["score"] for r in g[t]) for t in g)
    cost[arm] = st.mean(r["cost"] for r in rs)

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("Splitting a feature across three coders scored no better than one agent, at over twice the cost",
             x=0.01, ha="left", fontsize=14, y=0.96)
a1 = fig.add_axes([0.30, 0.14, 0.36, 0.66]); a2 = fig.add_axes([0.72, 0.14, 0.24, 0.66])
ys = list(range(len(ARMS) - 1, -1, -1))
for ax, vals, title, fmt, xmax, col in (
        (a1, score, "Hidden tests passed (higher is better)", "{:.1f}%", 100, TEAL),
        (a2, cost, "Cost per run (lower is better)", "${:.3f}", 0.24, MID)):
    for y, (arm, _, _) in zip(ys, ARMS):
        v = vals[arm]
        ax.barh(y, v, height=0.62, color=NAVY if (ax is a1 and arm == "solo") else col)
        ax.text(v + xmax * 0.015, y, fmt.format(v), va="center", fontsize=8.5, color=NAVY)
    ax.set_xlim(0, xmax * 1.18)
    ax.set_title(title, fontsize=10.5, loc="left")
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
a1.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"], fontsize=9)
a2.set_xticks([0, 0.1, 0.2], ["$0", "$0.10", "$0.20"], fontsize=9)
a1.set_yticks(ys, [a[1] for a in ARMS], fontsize=9)
a2.set_yticks(ys, [""] * len(ARMS))
fig.text(0.01, 0.02, SOURCE, fontsize=7.5, color=MUTED)
p = os.path.join(OUT, "chart-sps-split.png")
fig.savefig(p, facecolor="white")
print(p, {k: round(v, 1) for k, v in score.items()}, {k: round(v, 3) for k, v in cost.items()})
