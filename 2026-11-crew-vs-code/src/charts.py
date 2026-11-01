"""Draws the chart used in the article, from results/main/runs.jsonl.gz and judge.jsonl.gz.

Usage: uv run --with matplotlib python3 -I src/charts.py [Inter font dir]   (writes results/chart-crew-vs-code.png)
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal.
Left: share of runs resolved per level, for the four architectures with Luna (higher is better).
Right: share of runs whose reply claims an action the shop's log doesn't show, per architecture and model (lower is
better).
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
SOURCE = ("Source: github.com/meabs/experiments, 2026-11-crew-vs-code/results (OpenRouter, default settings). "
          "38 emails × 2 wordings × 2 account sizes × 5 runs = 760 runs per architecture and model.")
runs = [json.loads(l) for l in gzip.open(os.path.join(ROOT, "results", "main", "runs.jsonl.gz"), "rt")]
judge = {j["key"]: j for j in map(json.loads, gzip.open(os.path.join(ROOT, "results", "main", "judge.jsonl.gz"), "rt"))}
BACK = {"refund": {"refund", "cancel"}, "replacement": {"replace"}, "cancel": {"cancel"}, "address_change": {"address"},
        "handed_to_team": {"escalate"}}     # as in analyse.py
for r in runs:
    j = judge[f"{r['case']}|{r['wording']}|{r['history']}|{r['arm']}|{r['model']}|{r['rep']}"]
    t = {a["type"] for a in r["actions"]}
    r["false_claim"] = any(j.get(c) is True and not t & b for c, b in BACK.items())
LUNA, QWEN = "openai/gpt-6-luna", "qwen/qwen3.7-flash"
ARMS = [("statemachine", "State machine", LIGHT), ("agent", "Single agent", BEIGE),
        ("crew_note", "Crew, note only", MUTED), ("crew_shared", "Crew, full history", TEAL)]
LEVELS = ["1 simple", "2 multi-\nstep", "3 branch-\ning", "4 recovery", "5 other", "6 compound\n(new)"]


def sel(arm, model, **kw):
    return [r for r in runs if r["arm"] == arm and r["model"] == model and all(r[k] == v for k, v in kw.items())]


plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("The crew did worst on the emails it was meant to win, and claimed work nobody did",
             x=0.01, ha="left", fontsize=11.5, y=0.96)
a1 = fig.add_axes([0.06, 0.2, 0.52, 0.56]); a2 = fig.add_axes([0.74, 0.2, 0.24, 0.56])
w = 0.2
for i, (arm, name, col) in enumerate(ARMS):
    vals = []
    for lv in range(1, 7):
        rs = sel(arm, LUNA, level=lv)
        vals.append(100 * sum(r["outcome"] == "resolved" for r in rs) / len(rs))
    a1.bar([x + (i - 1.5) * w for x in range(6)], vals, width=w, color=col, label=name)
a1.set_xticks(range(6), LEVELS, fontsize=8)
a1.set_ylim(0, 100); a1.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"], fontsize=8)
a1.set_title("Runs resolved, by level (Luna; higher is better)", fontsize=9.5, loc="left")
a1.legend(loc="upper left", bbox_to_anchor=(0, 1.2), ncol=4, frameon=False, fontsize=8, handlelength=1)
ys = list(range(len(ARMS)))[::-1]
h = 0.38
for y, (arm, name, _) in zip(ys, ARMS):
    for k, (model, col, lab) in enumerate([(LUNA, TEAL, "Luna"), (QWEN, BEIGE, "Qwen")]):
        rs = sel(arm, model); v = 100 * sum(r["false_claim"] for r in rs) / len(rs)
        a2.barh(y + (0.5 - k) * h, v, height=h, color=col, label=lab if y == ys[0] else None)
        a2.text(v + 0.6, y + (0.5 - k) * h, f"{v:.0f}%", va="center", fontsize=7.5)
a2.set_yticks(ys, [n for _, n, _ in ARMS], fontsize=8)
a2.set_xlim(0, 22); a2.set_xticks([0, 10, 20], ["0%", "10%", "20%"], fontsize=8)
a2.set_title("Replies claiming an action\nthat wasn't taken (lower is better)", fontsize=9.5, loc="left")
a2.legend(loc="upper left", bbox_to_anchor=(-0.6, -0.08), ncol=2, frameon=False, fontsize=7.5, handlelength=1)
for ax in (a1, a2):
    ax.set_axisbelow(True); ax.tick_params(length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
a1.grid(axis="y", color=GRID); a2.grid(axis="x", color=GRID)
fig.text(0.01, 0.025, SOURCE, fontsize=6.6, color=MUTED)
p = os.path.join(ROOT, "results", "chart-crew-vs-code.png")
fig.savefig(p, facecolor="white")
print(p)
