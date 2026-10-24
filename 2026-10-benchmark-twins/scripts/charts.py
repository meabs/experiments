"""Draws the chart used on the website write-up, from the exported answers.

Usage: uv run --with matplotlib python3 -I charts.py <results stage dir, e.g. results/main> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and diff-judge's charts.py): 1800 x 920 px, Inter, beige / teal.
Scores are the preregistered grades (no regrading).
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


def right(model, bench, variant, only=None):
    rs = [json.load(open(f)) for f in glob.glob(os.path.join(D, model, bench, variant, "*", "result.json"))]
    rs = [r for r in rs if only is None or r["idx"] in only]
    return sum(r["correct"] for r in rs), len(rs)


def idxs(model, bench, variant):
    return {int(os.path.basename(os.path.dirname(f))) for f in glob.glob(os.path.join(D, model, bench, variant, "*", "result.json"))}


TEAL, BEIGE, NAVY, MUTED, GRID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed"
# (label, benchmark, twin variant); the names comparison uses only the 64 items that have a names twin
ROWS = [("GSM8K: new numbers", "gsm8k", "numbers"), ("GSM8K: new names", "gsm8k", "names"),
        ("HumanEval: function renamed", "humaneval", "renamed")]
MODELS = [("local", "qwen3.8:27b on this machine"), ("hosted", "gpt-5.6-luna, hosted")]
SOURCE = "Source: github.com/meabs/experiments, 2026-10-benchmark-twins/results (Codex CLI, low reasoning; preregistered grades)."

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig, axes = plt.subplots(1, 2, figsize=(9, 4.6), dpi=200, sharey=True)
fig.subplots_adjust(left=0.25, right=0.97, top=0.74, bottom=0.2, wspace=0.12)
fig.suptitle("Scores barely moved on the twins", x=0.01, ha="left", fontsize=15, y=0.95)
H = 0.36
for ax, (model, title) in zip(axes, MODELS):
    for i, (_, bench, var) in enumerate(ROWS):
        only = idxs(model, bench, var)
        y = len(ROWS) - 1 - i
        for dy, v, c in ((H / 2 + 0.02, "orig", TEAL), (-H / 2 - 0.02, var, BEIGE)):
            k, n = right(model, bench, v, only)
            pct = 100 * k / n
            ax.barh(y + dy, pct, height=H, color=c)
            ax.text(pct + 1.5, y + dy, f"{k}/{n}", va="center", fontsize=9,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.5))
    ax.set_title(title, fontsize=11.5, loc="left")
    ax.set_xlim(0, 118); ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    ax.tick_params(axis="x", labelsize=9.5)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_yticks(range(len(ROWS)), [r[0] for r in reversed(ROWS)])
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=TEAL), plt.Rectangle((0, 0), 1, 1, color=BEIGE)],
           labels=["Original item", "Twin"], loc="upper left", bbox_to_anchor=(0.01, 0.89), ncol=2,
           frameon=False, fontsize=10.5)
fig.text(0.01, 0.02, SOURCE, fontsize=8.5, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-bt-twins.png"), facecolor="white")
print(os.path.join(OUT, "chart-bt-twins.png"))
