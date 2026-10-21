"""Draws the four charts used on the website write-up, from the raw runs (via analyse.py's rows).

Usage: uv run --with matplotlib python3 -I charts.py <runs dir> <out dir> [font dir]
Style follows the Programming the Loop guide charts: 1800 x 920 px, Inter, beige / teal, source line at the foot.
"""
import contextlib, io, os, runpy, statistics as st, sys

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
rows, tasks, cell, passes, boot = g["rows"], g["tasks"], g["cell"], g["passes"], g["boot"]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
ARMS = ["none", "placebo", "superpowers", "pocock"]
LABEL = {"none": "No skills", "placebo": "Placebo skill", "superpowers": "Superpowers", "pocock": "Pocock"}
SOURCE = "Source: github.com/meabs/experiments, 2026-10-skills-tasks/results/stage1 (Codex gpt-5.6-luna, low reasoning)."
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
fig, ax = figure("Hidden tests passed, by task (2 runs per arm per task)")
fig.subplots_adjust(left=0.15, right=0.9, bottom=0.24)
shade = {0: PALE, 1: BEIGE, 2: TEAL}
for y, a in enumerate(reversed(ARMS)):
    for x, t in enumerate(tasks):
        p = passes(t, a)
        ax.add_patch(plt.Rectangle((x + 0.04, y + 0.06), 0.92, 0.88, color=shade[p], lw=0))
        ax.text(x + 0.5, y + 0.5, str(p), ha="center", va="center", fontsize=11, color="white" if p == 2 else NAVY)
    ax.text(len(tasks) + 0.25, y + 0.5, f"{sum(passes(t, a) for t in tasks)}/32", va="center", fontsize=12, fontweight="semibold")
ax.set_xlim(0, len(tasks)); ax.set_ylim(0, len(ARMS))
ax.set_xticks([i + 0.5 for i in range(len(tasks))], tasks, rotation=55, ha="right", fontsize=9.5)
ax.set_yticks([i + 0.5 for i in range(len(ARMS))], [LABEL[a] for a in reversed(ARMS)])
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
save(fig, "chart-skt-passes.png", "Cell: runs passed of 2.")

# 2. Per-task token ratio to the no-skills arm.
fig, ax = figure("Tokens per task, relative to the no-skills arm")
fig.subplots_adjust(left=0.18)
for y, a in enumerate(["placebo", "pocock", "superpowers"]):
    ratios = [st.mean(r["tokens"] for r in cell[(t, a)]) / st.mean(r["tokens"] for r in cell[(t, "none")]) for t in tasks]
    lo, hi = boot(ratios)
    ax.scatter(ratios, [y + (i % 5 - 2) * 0.05 for i in range(len(ratios))], s=28, color=BEIGE, zorder=2)
    ax.plot([lo, hi], [y + 0.28] * 2, color=TEAL, lw=3, solid_capstyle="butt")
    ax.scatter([st.mean(ratios)], [y + 0.28], s=70, color=TEAL, zorder=3)
    ax.text(hi + 0.08, y + 0.28, f"{st.mean(ratios):.2f}x ({lo:.2f} to {hi:.2f})", va="center", fontsize=11)
ax.axvline(1, color=MUTED, lw=1, ls="--")
ax.set_yticks(range(3), [LABEL[a] for a in ["placebo", "pocock", "superpowers"]])
ax.set_ylim(-0.5, 2.6)
ax.set_xlabel("Mean tokens per run, divided by the no-skills mean for the same task")
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0)
save(fig, "chart-skt-tokens.png", "Dots: tasks.")

# 3. Process: what the agent did, runs of 32.
fig, ax = figure("What the agent did, runs out of 32 per arm")
fig.subplots_adjust(left=0.24)
measures = [("Read a skill file", lambda r: r["skill"]),
            ("Ran Maven tests", lambda r: r["test_runs"] > 0),
            ("Wrote or changed tests", lambda r: r["test_lines"] > 0),
            ("Edited a test file first", lambda r: r["tff"] is True)]
colours = {"none": PALE, "placebo": BEIGE, "superpowers": TEAL, "pocock": NAVY}
h = 0.19
for i, (name, f) in enumerate(measures):
    for j, a in enumerate(ARMS):
        n = sum(bool(f(r)) for r in rows if r["arm"] == a)
        y = len(measures) - 1 - i + (1.5 - j) * h
        ax.barh(y, n, height=h, color=colours[a], label=LABEL[a] if i == 0 else None,
                edgecolor=BEIGE if a == "none" else "none", lw=0.6)
        ax.text(n + 0.3, y, str(n), va="center", fontsize=9)
ax.set_yticks(range(len(measures)), [m for m, _ in reversed(measures)])
ax.set_xlim(0, 34); ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=10, loc="lower right")
save(fig, "chart-skt-process.png")

# 4. Outcome and what the agent said.
fig, ax = figure("Passed, or failed while saying it worked, runs out of 32")
fig.subplots_adjust(left=0.18)
for y, a in enumerate(reversed(ARMS)):
    rs = [r for r in rows if r["arm"] == a]
    ok = sum(r["passed"] for r in rs)
    over = sum(r["overclaim"] for r in rs if not r["passed"])
    rest = len(rs) - ok - over
    ax.barh(y, ok, color=TEAL, label="Passed" if y == 0 else None)
    ax.barh(y, over, left=ok, color=BEIGE, label="Failed, said it worked" if y == 0 else None)
    ax.barh(y, rest, left=ok + over, color=NAVY, label="Failed, did not claim it worked" if y == 0 else None)
    ax.text(ok / 2, y, str(ok), ha="center", va="center", color="white", fontsize=11)
    ax.text(ok + over / 2, y, str(over), ha="center", va="center", fontsize=11)
ax.set_yticks(range(len(ARMS)), [LABEL[a] for a in reversed(ARMS)])
ax.set_xlim(0, 32); ax.tick_params(axis="y", length=0)
ax.legend(frameon=False, fontsize=10, ncol=3, loc="upper left", bbox_to_anchor=(0, -0.1))
fig.subplots_adjust(bottom=0.26)
save(fig, "chart-skt-claims.png")
print("wrote 4 charts to", OUT)
