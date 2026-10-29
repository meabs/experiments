"""Draws the website chart from demo/results.json.

Usage: uv run --with matplotlib python3 -I demo/chart.py [Inter font dir]   (writes demo/chart-webmcp-demo.png)
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal.
Left: buggy versions caught, by the ordinary check and by WebMCP Resilience (higher is better). Right: false alarms
on correct versions (lower is better).
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

TEAL, BEIGE, NAVY, MUTED, GRID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-webmcp-resilience/demo (WebMCP Resilience 0.1.0, 14 scenarios, "
          "each run 3 times; ground truth: hidden Playwright tests).")
r = json.load(open(os.path.join(D, "results.json"))).values()
GROUPS = [("buggy original", "Buggy originals"), ("planted wrong fix", "Plausible wrong fixes"), ("agent fix", "Agent's wrong fix")]
rows = []
for kind, label in GROUPS:
    b = [v for v in r if v["kind"] == kind and v["buggy"]]
    rows.append((label, len(b), sum(v["ordinary_catches"] for v in b), sum(v["tool_catches"] for v in b)))
good = [v for v in r if not v["buggy"]]
fa_ord, fa_tool = sum(v["ordinary_catches"] for v in good), sum(v["tool_catches"] for v in good)

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("An ordinary check caught none of 19 timing bugs; WebMCP Resilience caught 11",
             x=0.01, ha="left", fontsize=13, y=0.96)
a1 = fig.add_axes([0.22, 0.16, 0.44, 0.62]); a2 = fig.add_axes([0.74, 0.16, 0.22, 0.62])
ys = [2, 1, 0]
h = 0.36
for y, (label, n, o, t) in zip(ys, rows):
    a1.barh(y + h / 2, o, height=h, color=BEIGE)
    a1.barh(y - h / 2, t, height=h, color=TEAL)
    a1.text(o + 0.2, y + h / 2, f"{o} of {n} ordinary check", va="center", fontsize=8, color=NAVY)
    a1.text(t + 0.2, y - h / 2, f"{t} of {n} WebMCP Resilience", va="center", fontsize=8, color=NAVY)
a1.set_xlim(0, 15); a1.set_xticks([0, 4, 8, 12], ["0", "4", "8", "12"], fontsize=9)
a1.set_title("Buggy versions caught (higher is better)", fontsize=10, loc="left")
a1.set_yticks(ys, [g[0] for g in rows], fontsize=9)
a2.barh([1], [fa_ord], height=0.5, color=BEIGE); a2.barh([0], [fa_tool], height=0.5, color=TEAL)
a2.text(0.3, 1, f"{fa_ord} of {len(good)} ordinary check", va="center", fontsize=8, color=NAVY)
a2.text(0.3, 0, f"{fa_tool} of {len(good)} WebMCP Resilience", va="center", fontsize=8, color=NAVY)
a2.set_xlim(0, 12); a2.set_xticks([0, 6, 12], ["0", "6", "12"], fontsize=9); a2.set_yticks([1, 0], ["", ""])
a2.set_title("False alarms on correct\nversions (lower is better)", fontsize=10, loc="left")
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.03, SOURCE, fontsize=7, color=MUTED)
p = os.path.join(D, "chart-webmcp-demo.png")
fig.savefig(p, facecolor="white")
print(p, rows, fa_ord, fa_tool)
