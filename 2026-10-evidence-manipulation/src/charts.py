"""Draws the chart used on the website write-up, from results/<stage>/scores.jsonl (written by analyse.py).

Usage: uv run --with matplotlib python3 -I src/charts.py <results stage dir, e.g. results/main> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and planted-errors' charts.py): 1800 x 920 px, Inter, beige / teal.
Left: correct decisions by condition. Right: runs where the agent flagged suspected manipulation, by condition.
"""
import json, os, sys

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
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-evidence-manipulation/results "
          "(qwen3.8:27b Q4_K_M via Ollama; 40 scenarios × 3 seeds per condition).")
CONDS = [("clean", "Clean"), ("falsified", "Falsified fact"), ("injection", "Injected instruction"), ("combined", "Both"),
         ("falsified_v", "Falsified + verify"), ("injection_v", "Injected + verify"), ("combined_v", "Both + verify")]

S = [json.loads(l) for l in open(os.path.join(D, "scores.jsonl"))]
rate = {c: {k: sum(s[k] for s in S if s["condition"] == c) for k in ("correct", "detected")} for c, _ in CONDS}
n = {c: sum(1 for s in S if s["condition"] == c) for c, _ in CONDS}

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("A falsified fact misled the agent; an injected instruction changed no decisions", x=0.01, ha="left", fontsize=14.5, y=0.96)
a1 = fig.add_axes([0.22, 0.14, 0.33, 0.66]); a2 = fig.add_axes([0.62, 0.14, 0.33, 0.66])

for ax, key, title, col in ((a1, "correct", "Correct decisions", TEAL), (a2, "detected", "Flagged suspected manipulation", MID)):
    for i, (c, _) in enumerate(CONDS):
        y = len(CONDS) - 1 - i - (0.4 if i >= 4 else 0)
        v = rate[c][key]; w = 100 * v / n[c]
        ax.barh(y, w, height=0.62, color=col if c not in ("falsified", "combined") or key != "correct" else NAVY)
        ax.text(w + 1.5, y, f"{v}/{n[c]}", va="center", fontsize=8.5, color=NAVY)
    ax.set_xlim(0, 118); ax.set_xticks([0, 50, 100], ["0%", "50%", "100%"], fontsize=9)
    ax.set_title(title, fontsize=11, loc="left")
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
ys = [len(CONDS) - 1 - i - (0.4 if i >= 4 else 0) for i in range(len(CONDS))]
a1.set_yticks(ys, [c[1] for c in CONDS], fontsize=9)
a2.set_yticks(ys, [""] * len(CONDS))
fig.text(0.01, 0.02, SOURCE, fontsize=7.5, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-em-evidence.png"), facecolor="white")
print(os.path.join(OUT, "chart-em-evidence.png"), rate)
