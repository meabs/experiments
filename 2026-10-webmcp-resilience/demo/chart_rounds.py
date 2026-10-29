"""Draws the website chart for the follow-up: buggy versions caught in each round, from the three results files.

Usage: uv run --with matplotlib python3 -I demo/chart_rounds.py [Inter font dir]   (writes demo/chart-webmcp-rounds.png)
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal.
"""
import json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

D = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) > 1:
    for f in os.listdir(sys.argv[1]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[1], f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID, MID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#6f9aa8"
ROUNDS = [("results.json", "1. Original tool\n(with my workarounds)"),
          ("results-round2.json", "2. Fixed tool\n(no workarounds)"),
          ("results-round3.json", "3. + slow and out-of-order\nserver replies")]
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-webmcp-resilience/demo. Each check run 3 times; hidden tests "
          "decide which versions are buggy. Round 3: same apps, server calls over HTTP.")
rows = []
for f, label in ROUNDS:
    r = json.load(open(os.path.join(D, f))).values()
    rows.append((label, sum(v["tool_catches"] for v in r if v["buggy"]), sum(v["buggy"] for v in r),
                 sum(v["tool_catches"] for v in r if not v["buggy"]), sum(not v["buggy"] for v in r)))

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle(f"After the fixes, WebMCP Resilience caught {rows[-1][1]} of {rows[-1][2]} timing bugs, up from {rows[0][1]}",
             x=0.01, ha="left", fontsize=13, y=0.96)
a1 = fig.add_axes([0.25, 0.16, 0.42, 0.62]); a2 = fig.add_axes([0.75, 0.16, 0.21, 0.62])
ys = [2, 1, 0]
for y, (label, caught, n, fa, good) in zip(ys, rows):
    a1.barh(y, caught, height=0.55, color=TEAL if y == 0 else MID)
    a1.text(caught + 0.25, y, f"{caught} of {n}", va="center", fontsize=9, color=NAVY)
    a2.barh(y, fa, height=0.55, color=BEIGE)
    a2.text(fa + 0.3, y, f"{fa} of {good}", va="center", fontsize=9, color=NAVY)
a1.set_xlim(0, 21); a1.set_xticks([0, 5, 10, 15, 19], ["0", "5", "10", "15", "19"], fontsize=9)
a1.set_title("Buggy versions caught (higher is better)", fontsize=10, loc="left")
a1.set_yticks(ys, [r[0] for r in rows], fontsize=9)
a2.set_xlim(0, 12); a2.set_xticks([0, 6, 12], ["0", "6", "12"], fontsize=9); a2.set_yticks(ys, ["", "", ""])
a2.set_title("False alarms on correct\nversions (lower is better)", fontsize=10, loc="left")
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.03, SOURCE, fontsize=6.5, color=MUTED)
p = os.path.join(D, "chart-webmcp-rounds.png")
fig.savefig(p, facecolor="white")
print(p, rows)
