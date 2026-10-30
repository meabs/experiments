"""Draws the chart used in the article, from results/main/runs.jsonl.gz.

Usage: uv run --with matplotlib python3 -I src/charts.py [Inter font dir]   (writes results/chart-need-an-agent.png)
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal.
Left: share of runs resolved per level, for plain code and the three AI architectures with Luna (higher is better).
Right: how all 640 runs of each architecture-and-model ended: resolved, escalated, wrong, harmful.
"""
import gzip, json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1:
    for f in os.listdir(sys.argv[1]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[1], f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID, RED, LIGHT = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#b4532a", "#dcd7cb"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-need-an-agent/results (OpenRouter, default settings). "
          "32 emails × 2 wordings × 2 account sizes × 5 runs = 640 runs per row.")
runs = [json.loads(l) for l in gzip.open(os.path.join(ROOT, "results", "main", "runs.jsonl.gz"), "rt")]
LEFT = [("rules", "none", "Plain code", LIGHT), ("single", "openai/gpt-6-luna", "One model call", BEIGE),
        ("workflow", "openai/gpt-6-luna", "Workflow", MUTED), ("agent", "openai/gpt-6-luna", "Agent", TEAL)]
RIGHT = [("rules", "none", "Plain code"), ("single", "openai/gpt-6-luna", "One call, Luna"),
         ("single", "qwen/qwen3.7-flash", "One call, Qwen"), ("workflow", "openai/gpt-6-luna", "Workflow, Luna"),
         ("workflow", "qwen/qwen3.7-flash", "Workflow, Qwen"), ("agent", "openai/gpt-6-luna", "Agent, Luna"),
         ("agent", "qwen/qwen3.7-flash", "Agent, Qwen")]
LEVELS = ["1 simple", "2 multi-\nstep", "3 branch-\ning", "4 recovery", "5 unanti-\ncipated"]
OUTCOMES = [("resolved", TEAL, "Resolved"), ("escalated", "#d9b56a", "Escalated (safe, needs a person)"),
            ("wrong", LIGHT, "Wrong"), ("harmful", RED, "Harmful")]


def sel(arm, model, **kw):
    return [r for r in runs if r["arm"] == arm and r["model"] == model and all(r[k] == v for k, v in kw.items())]


plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("Simple and branching emails didn't need an agent; recovering from failures did",
             x=0.01, ha="left", fontsize=11.5, y=0.96)
a1 = fig.add_axes([0.06, 0.2, 0.47, 0.56]); a2 = fig.add_axes([0.72, 0.2, 0.26, 0.56])
w = 0.2
for i, (arm, model, name, col) in enumerate(LEFT):
    vals = []
    for lv in range(1, 6):
        rs = sel(arm, model, level=lv)
        vals.append(100 * sum(r["outcome"] == "resolved" for r in rs) / len(rs))
    a1.bar([x + (i - 1.5) * w for x in range(5)], vals, width=w, color=col, label=name)
a1.set_xticks(range(5), LEVELS, fontsize=8)
a1.set_ylim(0, 100); a1.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"], fontsize=8)
a1.set_title("Runs resolved, by level (Luna; higher is better)", fontsize=9.5, loc="left")
a1.legend(loc="upper left", bbox_to_anchor=(0, 1.2), ncol=4, frameon=False, fontsize=8, handlelength=1)
ys = list(range(len(RIGHT)))[::-1]
for y, (arm, model, name) in zip(ys, RIGHT):
    rs = sel(arm, model); left = 0
    for o, col, _ in OUTCOMES:
        v = 100 * sum(r["outcome"] == o for r in rs) / len(rs)
        a2.barh(y, v, left=left, color=col, height=0.7)
        left += v
a2.set_yticks(ys, [n for _, _, n in RIGHT], fontsize=8)
a2.set_xlim(0, 100); a2.set_xticks([0, 50, 100], ["0%", "50%", "100%"], fontsize=8)
a2.set_title("How runs ended, all levels", fontsize=9.5, loc="left")
a2.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, c, _ in OUTCOMES], labels=[l for *_, l in OUTCOMES],
          loc="upper left", bbox_to_anchor=(-0.55, -0.08), ncol=2, frameon=False, fontsize=7.2, handlelength=1)
for ax in (a1, a2):
    ax.set_axisbelow(True); ax.tick_params(length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
a1.grid(axis="y", color=GRID); a2.grid(axis="x", color=GRID)
fig.text(0.01, 0.025, SOURCE, fontsize=6.6, color=MUTED)
p = os.path.join(ROOT, "results", "chart-need-an-agent.png")
fig.savefig(p, facecolor="white")
print(p)
