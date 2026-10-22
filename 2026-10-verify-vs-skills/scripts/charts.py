"""Draws the four charts used on the website write-up, from the raw runs (via analyse.py's rows).

Usage: uv run --with matplotlib python3 -I charts.py <runs dir, low> <runs dir, medium> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and skills-tasks' charts.py): 1800 x 920 px, Inter, beige / teal.
"""
import contextlib, glob, io, os, runpy, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

LOW, MED, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
if len(sys.argv) > 4:
    for f in os.listdir(sys.argv[4]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[4], f))
    plt.rcParams["font.family"] = "Inter"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["analyse.py", LOW, MED]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(HERE, "analyse.py"))
rows, tasks, passes, detail = g["rows"], g["tasks"], g["passes"], g["detail"]

TEAL, BEIGE, NAVY, MUTED, GRID, PALE = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df"
ARMS = ["none", "verify", "superpowers", "medium"]
LABEL = {"none": "No skills (low)", "verify": "Verify instruction (low)", "superpowers": "Superpowers (low)",
         "medium": "Medium effort"}
SOURCE = "Source: github.com/meabs/experiments, 2026-10-verify-vs-skills/results (Codex gpt-5.6-luna)."
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
fig.subplots_adjust(left=0.25, right=0.9, bottom=0.24)
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
save(fig, "chart-vvs-passes.png", "Cell: runs passed of 3.")

# 2. Cost per verified pass, with the pass count.
fig, ax = figure("Cost per correct change (list prices)")
fig.subplots_adjust(left=0.26)
for y, a in enumerate(reversed(ARMS)):
    rs = [r for r in rows if r["arm"] == a]
    n = sum(r["passed"] for r in rs)
    c = sum(r["cost"] for r in rs) / n
    ax.barh(y, c * 100, color=TEAL if a == "medium" else BEIGE, height=0.6)
    ax.text(c * 100 + 0.1, y, f"{c * 100:.1f}¢   ({n} of 60 passed)", va="center", fontsize=11)
ax.set_yticks(range(len(ARMS)), [LABEL[a] for a in reversed(ARMS)])
ax.set_xlim(0, 10); ax.set_xlabel("US cents per run that passed (all runs' cost, divided by the runs that passed)")
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
save(fig, "chart-vvs-cost.png")

# 3. Process: what the agent did, runs of 60.
fig, ax = figure("What the agent did, runs out of 60 per arm")
fig.subplots_adjust(left=0.26)
det = {}
for runs, arms in [(LOW, ["none", "verify", "superpowers"]), (MED, ["medium"])]:
    for a in arms:
        det[a] = [detail(os.path.dirname(f)) for f in sorted(glob.glob(os.path.join(runs, "*", a, "codex", "*", "run.json")))]
measures = [("Tried to start the app", lambda a: sum(d[0] for d in det[a])),
            ("Got the app to answer", lambda a: sum(d[2] for d in det[a])),
            ("Ran the Maven tests", lambda a: sum(r["test_runs"] > 0 for r in rows if r["arm"] == a)),
            ("Wrote an API-level test", lambda a: sum(r["api_test"] for r in rows if r["arm"] == a))]
colours = {"none": PALE, "verify": BEIGE, "superpowers": NAVY, "medium": TEAL}
h = 0.19
for i, (name, f) in enumerate(measures):
    for j, a in enumerate(ARMS):
        n = f(a)
        y = len(measures) - 1 - i + (1.5 - j) * h
        ax.barh(y, n, height=h, color=colours[a], label=LABEL[a] if i == 0 else None,
                edgecolor=BEIGE if a == "none" else "none", lw=0.6)
        ax.text(n + 0.5, y, str(n), va="center", fontsize=9)
ax.set_yticks(range(len(measures)), [m for m, _ in reversed(measures)])
ax.set_xlim(0, 64); ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9.5, loc="lower right")
save(fig, "chart-vvs-process.png")

# 4. Outcome and what the agent said.
fig, ax = figure("Passed, or failed while saying it worked, runs out of 60")
fig.subplots_adjust(left=0.26)
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
ax.set_xlim(0, 60); ax.tick_params(axis="y", length=0)
ax.legend(frameon=False, fontsize=10, ncol=3, loc="upper left", bbox_to_anchor=(0, -0.1))
fig.subplots_adjust(bottom=0.26)
save(fig, "chart-vvs-claims.png")
print("wrote 4 charts to", OUT)
