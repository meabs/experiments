"""Draws the chart for the website write-up, from the exported results.

Usage: uv run --with matplotlib python3 -I src/charts.py <Inter font dir>   (reads results/main and results/investigate,
writes results/chart-team-herding.png)
Style follows the Programming the Loop guide charts (as sec-authz's charts.py): 1800 x 920 px, Inter, beige / teal.
Left: main run, falsified cases, harmful errors per arm: genuine threats called benign (of 20) and harmless activity
called malicious (of 22). Lower is better.
Right: the voting team (B) and the peer-reviewed team (C) on the 42 falsified case-repeats, without and with the option
to send conflicting evidence for investigation: right, sent for investigation, harmful error.
"""
import os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], os.path.join(ROOT, "results", "main"), os.path.join(ROOT, "results", "investigate")] + sys.argv[1:]
FONTS = sys.argv[3] if len(sys.argv) > 3 else None
import io, contextlib  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    import explore as X  # noqa: E402  (loads both runs; its printed tables are discarded here)

if FONTS:
    for f in os.listdir(FONTS):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(FONTS, f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID, MID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#6f9aa8"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-team-herding/results (Codex 0.157; gpt-5.6-luna team, gpt-5.6-sol "
          "reviewer; medium effort). 21 falsified scenarios × 2 repeats. Right panel: exploratory extra arm, run after the main run.")
ARMS = [("A", "One Luna agent"), ("B", "Three voting"), ("C", "Three after peer review"),
        ("E", "One agent, same token budget"), ("F", "Sol reviews the team"), ("G", "Sol alone")]


def count(B, a, group, what):
    return sum(X.arm_outcomes(B, c, k, a).get(a) == what for c, k in X.keys if X.kind(c) == group)


plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("Extra agents shared the same mistakes; a \"can't tell\" option halved harmful errors after peer review",
             x=0.01, ha="left", fontsize=11.5, y=0.96)
a1 = fig.add_axes([0.22, 0.25, 0.30, 0.54]); a2 = fig.add_axes([0.70, 0.25, 0.27, 0.54])

h = 0.36
ys = list(range(len(ARMS)))[::-1]
for y, (a, _) in zip(ys, ARMS):
    t, m = count(X.M, a, "threat", "harmful"), count(X.M, a, "harmless", "harmful")
    a1.barh(y + h / 2, t, height=h, color=TEAL)
    a1.barh(y - h / 2, m, height=h, color=BEIGE)
    a1.text(t + 0.4, y + h / 2, f"{t}/20", va="center", fontsize=7.5)
    a1.text(m + 0.4, y - h / 2, f"{m}/22", va="center", fontsize=7.5)
a1.set_yticks(ys, [n for _, n in ARMS], fontsize=8.5)
a1.set_xlim(0, 26); a1.set_xticks([0, 10, 20], ["0", "10", "20"], fontsize=8.5)
a1.set_title("Harmful errors (lower is better)", fontsize=9.5, loc="left")
a1.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=TEAL), plt.Rectangle((0, 0), 1, 1, color=BEIGE)],
          labels=["real threat called harmless, of 20", "harmless activity escalated, of 22"],
          fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(-0.02, -0.11), ncol=1)

rows = [("B", X.M, "Three voting"), ("B", X.I, "Three voting, can't-tell allowed"),
        ("C", X.M, "Three after peer review"), ("C", X.I, "Peer review, can't-tell allowed")]
ys2 = [3, 2, 1, 0]
for y, (a, B, label) in zip(ys2, rows):
    o = [X.arm_outcomes(B, c, k, a).get(a) for c, k in X.keys if X.kind(c) != "clean"]
    r, d, hm = o.count("right"), o.count("deferred"), o.count("harmful")
    a2.barh(y, r, height=0.55, color=TEAL)
    a2.barh(y, d, left=r, height=0.55, color=MID, hatch="///", edgecolor="white", linewidth=0)
    a2.barh(y, hm, left=r + d, height=0.55, color=BEIGE)
    for x0, v in ((0, r), (r, d), (r + d, hm)):
        if v >= 3:
            a2.text(x0 + v / 2, y, str(v), va="center", ha="center", fontsize=7.5, color="white" if x0 < r else NAVY)
a2.set_yticks(ys2, [r[2] for r in rows], fontsize=7.5)
a2.set_xlim(0, 42); a2.set_xticks([0, 21, 42], ["0", "21", "42"], fontsize=8.5)
a2.set_title("Falsified cases, of 42\n(more right, fewer harmful: better)", fontsize=9.5, loc="left")
a2.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=TEAL), plt.Rectangle((0, 0), 1, 1, color=MID, hatch="///", ec="white"),
                   plt.Rectangle((0, 0), 1, 1, color=BEIGE)],
          labels=["right", "sent for investigation", "harmful error"], fontsize=7, frameon=False, ncol=3,
          loc="upper left", bbox_to_anchor=(-0.16, -0.11), handlelength=1.4, columnspacing=1.0)
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.text(0.01, 0.025, SOURCE, fontsize=5.6, color=MUTED)
p = os.path.join(ROOT, "results", "chart-team-herding.png")
fig.savefig(p, facecolor="white")
print(p)
