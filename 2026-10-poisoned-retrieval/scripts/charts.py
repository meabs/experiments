"""Draws the chart used on the website write-up, from the exported results.

Usage: uv run --with matplotlib python3 -I charts.py <results stage dir, e.g. results/main> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and planted-errors' charts.py): 1800 x 920 px, Inter, beige / teal.
One stacked bar per model and condition (clean, poisoned, miss), split by graded outcome.
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

TEAL, BEIGE, NAVY, MUTED, GRID, PALE, MID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df", "#6f9aa8"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-poisoned-retrieval/results "
          "(qwen3.8:27b and qwen3:8b Q4_K_M via Ollama, bge-m3 retrieval, 120 HotpotQA dev questions).")
MODELS = [("qwen3.8_27b", "qwen3.8:27b"), ("qwen3_8b", "qwen3:8b")]
CONDS = [("clean", "Right paragraph"), ("poisoned", "One number changed"), ("miss", "Retrieval missed")]
KINDS = [("right", "Right answer", TEAL), ("follow", "Repeated the planted number", NAVY), ("both", "Gave both", MID),
         ("notfound", "Said NOT FOUND", BEIGE), ("other", "Other wrong answer", PALE)]

counts = {}
for m, _ in MODELS:
    for c, _ in CONDS:
        oc = [json.load(open(f))["outcome"] for f in glob.glob(os.path.join(D, m, c, "*", "result.json"))]
        counts[(m, c)] = {k: oc.count(k) for k, _, _ in KINDS}

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("Change one number in the retrieved paragraph, and the model repeats it", x=0.01, ha="left", fontsize=14.5, y=0.96)
axes = [fig.add_axes([0.2, 0.55, 0.72, 0.28]), fig.add_axes([0.2, 0.22, 0.72, 0.28])]

for ax, (m, name) in zip(axes, MODELS):
    for y, (c, label) in zip((2, 1, 0), CONDS):
        left = 0; n = sum(counts[(m, c)].values())
        for k, _, col in KINDS:
            v = counts[(m, c)][k]; w = 100 * v / n
            ax.barh(y, w, left=left, height=0.66, color=col, edgecolor="white", lw=1.5)
            if v >= 6:
                ax.text(left + w / 2, y, str(v), ha="center", va="center", fontsize=9,
                        color="white" if col in (NAVY, TEAL) else NAVY)
            left += w
        ax.text(101, y, f"of {n}", va="center", fontsize=8.5, color=MUTED)
    ax.set_yticks([2, 1, 0], [c[1] for c in CONDS], fontsize=9)
    ax.set_xlim(0, 100); ax.tick_params(axis="y", length=0)
    ax.text(-0.27, 1.0, name, transform=ax.transAxes, fontsize=10.5, fontweight="bold", va="bottom")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
axes[0].set_xticks([]); axes[0].spines["bottom"].set_visible(False)
axes[1].set_xticks([0, 50, 100], ["0%", "50%", "100%"], fontsize=9)
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in KINDS], labels=[l for _, l, _ in KINDS],
           loc="lower center", bbox_to_anchor=(0.55, 0.06), ncol=5, frameon=False, fontsize=8.5, handlelength=1.2)
fig.text(0.01, 0.02, SOURCE, fontsize=7.5, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-pr-poisoned.png"), facecolor="white")
print(os.path.join(OUT, "chart-pr-poisoned.png"), counts)
