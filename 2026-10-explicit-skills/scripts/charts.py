"""Draws the four charts used on the website write-up, from the raw runs (via analyse.py's rows).
The fourth also uses repo-skills' runs (via its own analyse.py), to show reading against doing across both experiments.

Usage: uv run --with matplotlib python3 -I charts.py <runs dir> <runs dir, arm D> <repo-skills runs dir> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and repo-skills' charts.py): 1800 x 920 px, Inter, beige / teal.
"""
import contextlib, io, os, runpy, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUNS, RUNS_D, RUNS_RSK, OUT = sys.argv[1:5]
if len(sys.argv) > 5:
    for f in os.listdir(sys.argv[5]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[5], f))
    plt.rcParams["font.family"] = "Inter"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["analyse.py", RUNS, RUNS_D]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(HERE, "analyse.py"))
rows, tasks, passes, cost_per_pass = g["rows"], g["tasks"], g["passes"], g["cost_per_pass"]
sys.argv = ["analyse.py", RUNS_RSK]
with contextlib.redirect_stdout(io.StringIO()):
    rsk_rows = runpy.run_path(os.path.join(HERE, "..", "..", "2026-10-repo-skills", "scripts", "analyse.py"))["rows"]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
MID = "#6f9aa8"
ARMS = ["none", "discover", "explicit", "agentsmd"]
LABEL = {"none": "No guidance", "discover": "Guidance, left to discover",
         "explicit": "Told in the prompt", "agentsmd": "Told in AGENTS.md"}
COLOUR = {"none": PALE, "discover": BEIGE, "explicit": MID, "agentsmd": TEAL}
SOURCE = "Source: github.com/meabs/experiments, 2026-10-explicit-skills/results (Codex gpt-5.6-luna, low reasoning)."
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
fig.subplots_adjust(left=0.28, right=0.9, bottom=0.3, top=0.86)
shade = {0: PALE, 1: BEIGE, 2: MID, 3: TEAL}
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
save(fig, "chart-esk-passes.png", "Cell: runs passed of 3.")

# 2. What the agent did, runs of 60.
fig, ax = figure("What the agent did, runs out of 60 per arm")
fig.subplots_adjust(left=0.3)
measures = [("Read verify-api skill", lambda r: "verify-api" in r["skills_read"]),
            ("Ran Maven tests", lambda r: r["test_runs"] > 0),
            ("API test detected\nin the change", lambda r: r["api_test"])]
h = 0.2
for i, (name, f) in enumerate(measures):
    for j, a in enumerate(ARMS):
        n = sum(bool(f(r)) for r in rows if r["arm"] == a)
        y = len(measures) - 1 - i + (1.5 - j) * h
        ax.barh(y, n, height=h, color=COLOUR[a], label=LABEL[a] if i == 0 else None,
                edgecolor=BEIGE if a == "none" else "none", lw=0.6)
        ax.text(n + 0.5, y, str(n), va="center", fontsize=9)
ax.set_yticks(range(len(measures)), [m for m, _ in reversed(measures)])
ax.set_xlim(0, 66); ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9.5, loc="lower right")
save(fig, "chart-esk-process.png")

# 3. Cost per verified pass.
fig, ax = figure("Cost per correct change (US cents, list prices)")
fig.subplots_adjust(left=0.3)
for i, a in enumerate(ARMS):
    v = cost_per_pass(tasks, a) * 100
    y = len(ARMS) - 1 - i
    ax.barh(y, v, height=0.6, color=COLOUR[a], edgecolor=BEIGE if a == "none" else "none", lw=0.6)
    ax.text(v + 0.08, y, f"{v:.1f}¢", va="center", fontsize=11)
ax.set_yticks(range(len(ARMS)), [LABEL[a] for a in reversed(ARMS)])
ax.set_xlim(0, 6.5); ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
save(fig, "chart-esk-cost.png", "Arm spend / verified passes.")

# 4. Reading against doing, across repo-skills and this experiment.
fig, axes = plt.subplots(1, 3, figsize=(9, 4.6), dpi=200, sharey=True)
fig.subplots_adjust(left=0.27, right=0.97, top=0.78, bottom=0.2, wspace=0.12)
fig.suptitle("Reading the verification skill is not the same as testing the change", x=0.01, ha="left", fontsize=15, y=0.95)
groups = [("Repository skills: no guidance", rsk_rows, "none", PALE),
          ("Repository skills: left to discover", rsk_rows, "repo-skills", BEIGE),
          ("This one: no guidance", rows, "none", PALE),
          ("This one: left to discover", rows, "discover", BEIGE),
          ("This one: told in the prompt", rows, "explicit", MID),
          ("This one: told in AGENTS.md", rows, "agentsmd", TEAL)]
panels = [("Read verify-api", lambda r: "verify-api" in r["skills_read"]),
          ("API test detected\nin the change", lambda r: r["api_test"]),
          ("Passed the\nhidden tests", lambda r: r["passed"])]
for ax, (title, f) in zip(axes, panels):
    for i, (name, rs, a, c) in enumerate(groups):
        n = sum(bool(f(r)) for r in rs if r["arm"] == a)
        y = len(groups) - 1 - i
        ax.barh(y, n, height=0.62, color=c, edgecolor=BEIGE if c == PALE else "none", lw=0.6)
        ax.text(n + 1.2, y, str(n), va="center", fontsize=9.5)
    ax.set_title(title, fontsize=11.5, loc="left")
    ax.set_xlim(0, 72); ax.set_xticks([0, 30, 60])
    ax.tick_params(axis="y", length=0, labelsize=10)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_yticks(range(len(groups)), [g[0] for g in reversed(groups)])
save(fig, "chart-esk-readdo.png", "Top two rows: 2026-10-repo-skills. Test detected from the diff.")
print("wrote 4 charts to", OUT)
