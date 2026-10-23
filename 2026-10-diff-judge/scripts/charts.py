"""Draws the chart used on the website write-up, from the exported judgements and items.json.

Usage: uv run --with matplotlib python3 -I charts.py <results stage dir, e.g. results/main> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and test-skill's charts.py): 1800 x 920 px, Inter, beige / teal.
"""
import glob, json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

D, OUT = sys.argv[1:3]
if len(sys.argv) > 3:
    for f in os.listdir(sys.argv[3]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[3], f))
    plt.rcParams["font.family"] = "Inter"

HERE = os.path.dirname(os.path.abspath(__file__)); N = os.path.dirname(HERE)
items = json.load(open(os.path.join(N, "items", "items.json")))
J = [json.load(open(f)) for f in glob.glob(os.path.join(D, "hosted", "*", "*", "judgement.json"))]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
MID = "#6f9aa8"
ROWS = [("agent", "The agent's own report", PALE), ("diff", "Judge: task and diff", TEAL),
        ("claim", "Judge: plus the agent's report", MID), ("hedge", "Judge: plus a doubtful report", BEIGE)]
SOURCE = "Source: github.com/meabs/experiments, 2026-10-diff-judge/results (judge: Codex gpt-5.6-luna, low reasoning)."


def count(key, truth):
    if key == "agent":
        return sum((i["passed"] == (truth == "PASS")) and ((i["claim"] == "passed") == (truth == "PASS")) for i in items)
    return sum(j["arm"] == key and j["truth"] == truth and j["verdict"] == truth for j in J)


plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig, axes = plt.subplots(1, 2, figsize=(9, 4.6), dpi=200, sharey=True)
fig.subplots_adjust(left=0.29, right=0.97, top=0.78, bottom=0.2, wspace=0.12)
fig.suptitle("The AI reviewer caught under half the broken changes", x=0.01, ha="left", fontsize=15, y=0.95)
panels = [("Broken changes called broken", "FAIL"), ("Working changes called working", "PASS")]
for ax, (title, truth) in zip(axes, panels):
    for i, (key, name, c) in enumerate(ROWS):
        n = count(key, truth)
        y = len(ROWS) - 1 - i
        ax.barh(y, n, height=0.62, color=c, edgecolor=BEIGE if c == PALE else "none", lw=0.6)
        ax.text(n + 0.9, y, str(n), va="center", fontsize=10, bbox=dict(facecolor="white", edgecolor="none", pad=1))
    ax.axvline(24, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.set_title(title, fontsize=11.5, loc="left")
    ax.set_xlim(0, 54); ax.set_xticks([0, 24, 48])
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_yticks(range(len(ROWS)), [r[1] for r in reversed(ROWS)])
fig.text(0.01, 0.02, SOURCE + " Out of 48 each; dashed line: a coin toss.", fontsize=8.5, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-dj-catch.png"), facecolor="white")
print(os.path.join(OUT, "chart-dj-catch.png"))
