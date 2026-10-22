"""Draws the four charts used on the website write-up, from the raw runs (via analyse.py's rows).

Usage: uv run --with matplotlib python3 -I charts.py <runs dir> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and skills-tasks' charts.py): 1800 x 920 px, Inter, beige / teal.
"""
import contextlib, glob, io, os, runpy, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUNS, OUT = sys.argv[1], sys.argv[2]
if len(sys.argv) > 3:
    for f in os.listdir(sys.argv[3]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[3], f))
    plt.rcParams["font.family"] = "Inter"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["analyse.py", RUNS]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(HERE, "analyse.py"))
rows, tasks, passes, detail = g["rows"], g["tasks"], g["passes"], g["detail"]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
ARMS = ["none", "repo-skills"]
LABEL = {"none": "No guidance", "repo-skills": "Repository guidance"}
SOURCE = "Source: github.com/meabs/experiments, 2026-10-repo-skills/results (Codex gpt-5.6-luna, low reasoning)."
plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})


def figure(title):
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200)
    fig.subplots_adjust(left=0.16, right=0.97, top=0.86, bottom=0.2)
    ax.set_title(title, loc="left", fontsize=16, pad=14)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return fig, ax


def save(fig, name, note=""):
    fig.text(0.01, 0.02, SOURCE + (" " + note if note else ""), fontsize=8.5, color=MUTED)
    fig.savefig(os.path.join(OUT, name), facecolor="white")
    plt.close(fig)


# 1. Passes per task and arm.
fig, ax = figure("Hidden tests passed, by task (3 runs per arm per task)")
fig.set_size_inches(9, 3.4)
fig.subplots_adjust(left=0.22, right=0.9, bottom=0.34, top=0.82)
shade = {0: PALE, 1: BEIGE, 2: "#6f9aa8", 3: TEAL}
for y, a in enumerate(reversed(ARMS)):
    for x, t in enumerate(tasks):
        p = passes(t, a)
        ax.add_patch(plt.Rectangle((x + 0.04, y + 0.06), 0.92, 0.88, color=shade[p], lw=0))
        ax.text(x + 0.5, y + 0.5, str(p), ha="center", va="center", fontsize=10, color="white" if p >= 2 else NAVY)
    ax.text(len(tasks) + 0.25, y + 0.5, f"{sum(passes(t, a) for t in tasks)}/60", va="center", fontsize=12, fontweight="semibold")
ax.set_xlim(0, len(tasks)); ax.set_ylim(0, len(ARMS))
ax.set_xticks([i + 0.5 for i in range(len(tasks))], tasks, rotation=55, ha="right", fontsize=8.5)
ax.set_yticks([i + 0.5 for i in range(len(ARMS))], [LABEL[a] for a in reversed(ARMS)])
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
save(fig, "chart-rsk-passes.png", "Cell: runs passed of 3.")

# 2. What the agent did with the guidance, runs of 60.
fig, ax = figure("What the agent did, runs out of 60 per arm")
fig.subplots_adjust(left=0.3)
measures = [("Read safe-change skill", lambda r: "safe-change" in r["skills_read"]),
            ("Read build-test skill", lambda r: "build-test" in r["skills_read"]),
            ("Read verify-api skill", lambda r: "verify-api" in r["skills_read"]),
            ("Ran Maven tests", lambda r: r["test_runs"] > 0),
            ("Wrote a test of its change", lambda r: r["test_lines"] > 0)]
colours = {"none": PALE, "repo-skills": TEAL}
h = 0.36
for i, (name, f) in enumerate(measures):
    for j, a in enumerate(ARMS):
        n = sum(bool(f(r)) for r in rows if r["arm"] == a)
        y = len(measures) - 1 - i + (0.5 - j) * h
        ax.barh(y, n, height=h, color=colours[a], label=LABEL[a] if i == 0 else None,
                edgecolor=BEIGE if a == "none" else "none", lw=0.6)
        ax.text(n + 0.5, y, str(n), va="center", fontsize=9.5)
ax.set_yticks(range(len(measures)), [m for m, _ in reversed(measures)])
ax.set_xlim(0, 64); ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=10, loc="lower right")
save(fig, "chart-rsk-process.png")
print("wrote 2 charts to", OUT)
