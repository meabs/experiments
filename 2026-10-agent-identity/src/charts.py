"""Draws the results chart for the write-up, from results/agent (runs.jsonl, calls.jsonl).

Usage: uv run --with matplotlib --with httpx python3 -I src/charts.py <Inter font dir>   (writes
results/chart-agent-identity.png)
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal.
Left: of 20 runs per setup, how often the agent tried a planted request, and how often it took effect (lower is better).
Right: legitimate tool calls refused or held, of all non-planted calls (lower is better).
"""
import json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_agents import injected  # noqa: E402

FONTS = sys.argv[1] if len(sys.argv) > 1 else None
if FONTS:
    for f in os.listdir(FONTS):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(FONTS, f))
    plt.rcParams["font.family"] = "Inter"

A = os.path.join(ROOT, "results", "agent")
runs = [json.loads(l) for l in open(os.path.join(A, "runs.jsonl"))]
calls = [json.loads(l) for l in open(os.path.join(A, "calls.jsonl"))]
TEAL, BEIGE, NAVY, MUTED, GRID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed"
SETUPS = [(1, "1. Shared key"), (2, "2. User's token\npassed through"), (3, "3. Agent service\naccount"),
          (4, "4. Delegated,\ntask-scoped")]
plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("The agent tried planted requests in every setup; the setup decided whether they worked",
             x=0.01, ha="left", fontsize=11.5, y=0.96)
a1 = fig.add_axes([0.17, 0.24, 0.36, 0.56]); a2 = fig.add_axes([0.72, 0.24, 0.25, 0.56])
h = 0.36
ys = [3, 2, 1, 0]
for y, (s, _) in zip(ys, SETUPS):
    rs = [r for r in runs if r["setup"] == s]
    tried = sum(r["outcome"]["attempted_injection"] for r in rs)
    harm = sum(r["outcome"]["harm"] for r in rs)
    a1.barh(y + h / 2, tried, height=h, color=BEIGE)
    a1.barh(y - h / 2, harm, height=h, color=TEAL)
    a1.text(tried + 0.3, y + h / 2, f"{tried}/{len(rs)}", va="center", fontsize=7.5)
    a1.text(harm + 0.3, y - h / 2, f"{harm}/{len(rs)}", va="center", fontsize=7.5)
a1.set_yticks(ys, [n for _, n in SETUPS], fontsize=8)
a1.set_xlim(0, 20); a1.set_xticks([0, 5, 10, 15, 20], ["0", "5", "10", "15", "20"], fontsize=8.5)
a1.set_title("Runs with a planted request, of 20 per setup", fontsize=9.5, loc="left")
a1.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BEIGE), plt.Rectangle((0, 0), 1, 1, color=TEAL)],
          labels=["agent tried it", "it took effect (lower is better)"], fontsize=7, frameon=False,
          loc="upper left", bbox_to_anchor=(-0.02, -0.11), ncol=2)
for y, (s, _) in zip(ys, SETUPS):
    cs = [c for c in calls if c["setup"] == s and not c.get("internal") and not injected(c["run"].split("-")[1], c)]
    bad = sum(c["outcome"] != "done" for c in cs)
    a2.barh(y, bad, height=0.5, color=TEAL)
    a2.text(bad + 0.4, y, f"{bad} of {len(cs)}", va="center", fontsize=7.5)
a2.set_yticks(ys, ["1", "2", "3", "4"], fontsize=8.5)
a2.set_xlim(0, 30); a2.set_xticks([0, 10, 20, 30], ["0", "10", "20", "30"], fontsize=8.5)
a2.set_title("Legitimate calls refused or held\n(lower is better)", fontsize=9.5, loc="left")
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.025, "Source: github.com/meabs/experiments, 2026-10-agent-identity/results (Codex 0.157, gpt-5.6-luna, "
         "medium effort; Keycloak 26.8.1). 4 tasks x 5 repeats per setup; one planted request per task.",
         fontsize=5.6, color=MUTED)
p = os.path.join(ROOT, "results", "chart-agent-identity.png")
fig.savefig(p, facecolor="white")
print(p)
