"""Draws the chart used on the website write-up of follow-up 2, from the graded runs and the line-name diagnostic.

Usage: uv run --with matplotlib python3 -I scripts/charts.py <out dir> [font dir]   (run from the pilot's folder)
Style follows the Programming the Loop guide charts (and test-skill's charts.py): 1800 x 920 px, Inter, beige / teal.
"""
import json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = sys.argv[1]
if len(sys.argv) > 2:
    for f in os.listdir(sys.argv[2]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[2], f))
    plt.rcParams["font.family"] = "Inter"

def strict(path):
    return sum(v == "pass" for v in json.load(open(path))["cases"].values())

def diag(name):
    return json.load(open(f"results/diagnostic-line-name/{name}.json"))["passed"]

MED = "results/baseline-discount-medium/runs/DISCOUNT/medium/codex"
RUNS = [("Plain Codex 1", f"{MED}/1/verify-summary.json", "base-med1"),
        ("Plain Codex 2", f"{MED}/2/verify-summary.json", "base-med2")]
RUNS += [(f"Plan + approver {i}", f"results/pa{i}/grade/verify-summary.json", f"pa{i}") for i in (1, 2, 3)]
RUNS += [(f"EGM + approver {i}", f"results/ea{i}/grade/verify-summary.json", f"ea{i}") for i in (1, 2, 3)]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
SOURCE = "Source: github.com/meabs/experiments, 2026-10-egm-pilot/results (Codex gpt-5.6-luna, medium reasoning)."
plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})

fig, axes = plt.subplots(1, 2, figsize=(9, 4.6), dpi=200, sharey=True)
fig.subplots_adjust(left=0.2, right=0.97, top=0.78, bottom=0.17, wspace=0.12)
fig.suptitle("An approver lifted both processes; EGM added nothing over a plain plan", x=0.01, ha="left", fontsize=14, y=0.95)
panels = [("Hidden tests passed, of 16", lambda r: strict(r[1])),
          ("Either line name accepted (diagnostic)", lambda r: diag(r[2]))]
for ax, (title, score) in zip(axes, panels):
    for i, r in enumerate(RUNS):
        n, y = score(r), len(RUNS) - 1 - i
        c = PALE if r[0].startswith("Plain") else TEAL if r[0].startswith("EGM") else BEIGE
        ax.barh(y, n, height=0.62, color=c, edgecolor=BEIGE if c == PALE else "none", lw=0.6)
        ax.text(n + 0.3, y, str(n), va="center", fontsize=10)
    ax.set_title(title, fontsize=11.5, loc="left")
    ax.set_xlim(0, 18); ax.set_xticks([0, 8, 16])
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_yticks(range(len(RUNS)), [r[0] for r in reversed(RUNS)])
fig.text(0.01, 0.02, SOURCE + " One bar per run.", fontsize=8.5, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-egm-approver.png"), facecolor="white")
print("wrote chart-egm-approver.png to", OUT)
