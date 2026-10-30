"""Draws the chart used on the website write-up, from the exported results (results/main/scored.json).

Usage: uv run --with matplotlib python3 -I scripts/charts.py results [Inter font dir]   (writes results/chart-repo-injection.png)
Style follows the Programming the Loop guide charts (as sec-authz's charts.py): 1800 x 920 px, Inter, beige / teal.
Left: runs hijacked by the disguised instruction, per channel, of 9 per arm (lower is better). The overt instruction
hijacked 0 of 45 runs in each arm, so it is given in a note, not drawn.
Right: over all 90 injected runs per arm, runs hijacked (lower is better) and runs whose final message told the user it
had not followed the instruction (higher is better; hand-checked counts, see results/checks.md).
"""
import json, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = sys.argv[1]
if len(sys.argv) > 2:
    for f in os.listdir(sys.argv[2]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[2], f))
    plt.rcParams["font.family"] = "Inter"

TEAL, BEIGE, NAVY, MUTED, GRID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed"
SOURCE = ("Source: github.com/meabs/experiments, 2026-10-repo-injection/results (Codex 0.157, gpt-5.6-luna, medium "
          "effort). 3 tasks × 3 runs per condition and arm. Overt instruction: 0 of 45 hijacked in each arm.")
CHANNELS = [("agents", "AGENTS.md"), ("ticket", "Ticket comment"), ("readme", "README"), ("code", "Code comment"),
            ("output", "Test output")]
TOLD = {"A": 15, "B": 89}  # hand-checked "told the user it did not follow it" (results/checks.md)

runs = [r for r in json.load(open(os.path.join(OUT, "main", "scored.json")))["runs"] if r["channel"] != "clean"]
dis = {(c, a): sum(r["hijacked"] for r in runs if r["channel"] == c and r["framing"] == "disguised" and r["arm"] == a)
       for c, _ in CHANNELS for a in "AB"}
hij = {a: sum(r["hijacked"] for r in runs if r["arm"] == a) for a in "AB"}

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("A setup script in AGENTS.md or the ticket hijacked every run; one prompt paragraph stopped almost all",
             x=0.01, ha="left", fontsize=12, y=0.96)
a1 = fig.add_axes([0.15, 0.13, 0.38, 0.58]); a2 = fig.add_axes([0.66, 0.13, 0.30, 0.58])
h = 0.36
ys = [4, 3, 2, 1, 0]
for y, (c, _) in zip(ys, CHANNELS):
    for a, dy, col in (("A", h / 2, BEIGE), ("B", -h / 2, TEAL)):
        a1.barh(y + dy, dis[(c, a)], height=h, color=col)
        a1.text(dis[(c, a)] + 0.2, y + dy, f"{dis[(c, a)]}/9", va="center", fontsize=8, color=NAVY)
a1.set_xlim(0, 11); a1.set_xticks([0, 3, 6, 9], ["0", "3", "6", "9"], fontsize=9)
a1.set_yticks(ys, [n for _, n in CHANNELS], fontsize=9)
a1.set_title("Disguised instruction (\"run scripts/dev-bootstrap.sh\"):\nruns hijacked, of 9 (lower is better)",
             fontsize=9.5, loc="left")
labels = [("Hijacked\n(lower is better)", hij), ("Told the user it\ndeclined (higher\nis better)", TOLD)]
for y, (lab, d) in zip([1, 0], labels):
    for a, dy, col in (("A", h / 2, BEIGE), ("B", -h / 2, TEAL)):
        a2.barh(y + dy, d[a], height=h, color=col)
        a2.text(d[a] + 1.5, y + dy, f"{d[a]}/90", va="center", fontsize=8, color=NAVY)
a2.set_xlim(0, 115); a2.set_xticks([0, 30, 60, 90], ["0", "30", "60", "90"], fontsize=9)
a2.set_yticks([1, 0], [lab for lab, _ in labels], fontsize=8.5)
a2.set_title("All 90 injected runs per arm", fontsize=9.5, loc="left")
for ax in (a1, a2):
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BEIGE), plt.Rectangle((0, 0), 1, 1, color=TEAL)],
           labels=["A: no defence", "B: one-paragraph defence in the prompt"], loc="upper left",
           bbox_to_anchor=(0.01, 0.91), ncol=2, frameon=False, fontsize=8.5)
fig.text(0.01, 0.03, SOURCE, fontsize=6.6, color=MUTED)
p = os.path.join(OUT, "chart-repo-injection.png")
fig.savefig(p, facecolor="white")
print(p, dis, hij)
