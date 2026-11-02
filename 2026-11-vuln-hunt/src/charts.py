"""Draws the chart used in the article, from results/main.

Usage: uv run --with matplotlib python3 -I src/charts.py [Inter font dir]   (writes results/chart-vuln-hunt.png)
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal.
Left: hard and very-hard vulnerabilities found per run (of 14), mean with worst and best run, Luna arms (higher is
better). Right: in how many of 10 runs each agent ran, Graph team against Swarm.
"""
import json, os, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import analyse

if len(sys.argv) > 1:
    for f in os.listdir(sys.argv[1]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[1], f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID, LIGHT = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#dcd7cb"
SOURCE = ("Source: github.com/meabs/experiments, 2026-11-vuln-hunt/results. gpt-5.6-luna, medium effort, 10 runs per arm; "
          "23 planted vulnerabilities, 14 of them hard or very hard.")
runs = analyse.load(ROOT / "results" / "main")
H = set(analyse.HARD)
ARMS = [("A", "Codex", BEIGE), ("A2", "Codex + checklist", BEIGE), ("B", "Strands specialist", LIGHT),
        ("C", "Strands team (Graph)", TEAL), ("D", "Strands swarm", LIGHT)]
AGENTS = [("recon", "Recon"), ("injection", "Injection"), ("access_auth", "Access control, auth"),
          ("crypto_config_deps", "Crypto, config, deps"), ("logic_integrity_errors", "Logic, integrity, errors"),
          ("verifier", "Verifier")]

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("A specialist prompt didn't beat Codex. A fixed team of specialists did; a swarm of the same agents didn't",
             x=0.01, ha="left", fontsize=11, y=0.96)
a1 = fig.add_axes([0.2, 0.2, 0.33, 0.6]); a2 = fig.add_axes([0.77, 0.2, 0.21, 0.6])
ys = list(range(len(ARMS)))[::-1]
for y, (arm, name, col) in zip(ys, ARMS):
    h = [len(r["found"] & H) for r in analyse.sel(runs, arm, "luna")]
    m = sum(h) / len(h)
    a1.barh(y, m, height=0.6, color=col)
    a1.plot([min(h), max(h)], [y, y], color=NAVY, lw=1)
    for x in (min(h), max(h)):
        a1.plot([x, x], [y - 0.12, y + 0.12], color=NAVY, lw=1)
    a1.text(max(h) + 0.3, y, f"{m:.1f}", va="center", fontsize=8.5)
a1.set_yticks(ys, [n for _, n, _ in ARMS], fontsize=8.5)
a1.set_xlim(0, 14); a1.set_xticks([0, 7, 14], ["0", "7", "14"], fontsize=8)
a1.set_title("Hard + very-hard found per run, of 14\n(mean; line = worst to best run; higher is better)",
             fontsize=9, loc="left")
ys2 = list(range(len(AGENTS)))[::-1]
hh = 0.38
for k, (arm, col, lab) in enumerate([("C", TEAL, "Graph team"), ("D", BEIGE, "Swarm")]):
    rs = analyse.sel(runs, arm, "luna")
    for y, (a, _) in zip(ys2, AGENTS):
        v = sum(a in set(r["handoffs"] or []) for r in rs)
        a2.barh(y + (0.5 - k) * hh, v, height=hh, color=col, label=lab if y == ys2[0] else None)
        a2.text(v + 0.2, y + (0.5 - k) * hh, str(v), va="center", fontsize=7.5)
a2.set_yticks(ys2, [n for _, n in AGENTS], fontsize=8)
a2.set_xlim(0, 11.5); a2.set_xticks([0, 5, 10], ["0", "5", "10"], fontsize=8)
a2.set_title("Runs in which each agent ran,\nof 10 (same agents and prompts)", fontsize=9, loc="left")
a2.legend(loc="upper left", bbox_to_anchor=(-0.8, -0.06), ncol=2, frameon=False, fontsize=7.5, handlelength=1)
for ax in (a1, a2):
    ax.set_axisbelow(True); ax.tick_params(length=0); ax.grid(axis="x", color=GRID)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.025, SOURCE, fontsize=6.6, color=MUTED)
p = ROOT / "results" / "chart-vuln-hunt.png"
fig.savefig(p, facecolor="white")
print(p)
