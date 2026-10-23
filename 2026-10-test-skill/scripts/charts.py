"""Draws the chart used on the website write-up, from the raw runs (via analyse.py's rows).

Usage: uv run --with matplotlib python3 -I charts.py <runs dir> <runs dir, medium> <runs dir, gate> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and explicit-skills' charts.py): 1800 x 920 px, Inter, beige / teal.
"""
import contextlib, io, os, runpy, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUNS, RUNS_E, RUNS_F, OUT = sys.argv[1:5]
if len(sys.argv) > 5:
    for f in os.listdir(sys.argv[5]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[5], f))
    plt.rcParams["font.family"] = "Inter"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["analyse.py", RUNS, RUNS_E, RUNS_F]
with contextlib.redirect_stdout(io.StringIO()):
    rows = runpy.run_path(os.path.join(HERE, "analyse.py"))["rows"]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
MID = "#6f9aa8"
ARMS = [("none", "No guidance", PALE), ("instruction", "Told to write a test", MID),
        ("skill", "Told, plus the skill", MID), ("skill-revised", "Told, plus the revised skill", MID),
        ("gate", "Gate: sent back once", TEAL), ("medium", "Medium effort", BEIGE)]
SOURCE = "Source: github.com/meabs/experiments, 2026-10-test-skill/results (Codex gpt-5.6-luna, low reasoning unless stated)."
plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})

fig, axes = plt.subplots(1, 2, figsize=(9, 4.6), dpi=200, sharey=True)
fig.subplots_adjust(left=0.27, right=0.97, top=0.78, bottom=0.2, wspace=0.12)
fig.suptitle("A real test of the change is not a correct change", x=0.01, ha="left", fontsize=15, y=0.95)
panels = [("Wrote a test that fails without\nthe change and passes with it", "relevant"), ("Passed the hidden tests", "passed")]
for ax, (title, key) in zip(axes, panels):
    for i, (a, name, c) in enumerate(ARMS):
        n = sum(r[key] for r in rows if r["arm"] == a)
        y = len(ARMS) - 1 - i
        ax.barh(y, n, height=0.62, color=c, edgecolor=BEIGE if c == PALE else "none", lw=0.6)
        ax.text(n + 1.2, y, str(n), va="center", fontsize=10)
    ax.set_title(title, fontsize=11.5, loc="left")
    ax.set_xlim(0, 70); ax.set_xticks([0, 30, 60])
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_yticks(range(len(ARMS)), [a[1] for a in reversed(ARMS)])
fig.text(0.01, 0.02, SOURCE + " Runs out of 60 per arm.", fontsize=8.5, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-ts-testpass.png"), facecolor="white")
print("wrote chart-ts-testpass.png to", OUT)
