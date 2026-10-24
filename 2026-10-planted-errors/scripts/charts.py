"""Draws the chart used on the website write-up, from the exported results.

Usage: uv run --with matplotlib python3 -I charts.py <results stage dir, e.g. results/main> <out dir> [font dir]
Style follows the Programming the Loop guide charts (and diff-judge's charts.py): 1800 x 920 px, Inter, beige / teal.
Left: forced-answer accuracy as more of the thinking is kept. Right: what happened to the planted errors (analysis set),
with recoveries split by where the fix happened (exploratory: the thinking's last number was the follow answer).
"""
import glob, json, os, re, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

D, OUT = sys.argv[1:3]
if len(sys.argv) > 3:
    for f in os.listdir(sys.argv[3]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[3], f))
    plt.rcParams["font.family"] = "Inter"

R = [json.load(open(f)) for f in glob.glob(os.path.join(D, "items", "*", "result.json"))]
NUMS = re.compile(r"\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?")
TEAL, BEIGE, NAVY, MUTED, GRID, PALE, MID = "#1f6f8b", "#b9b2a0", "#1d2a44", "#4a5873", "#e8eaed", "#ece8df", "#6f9aa8"
SOURCE = "Source: github.com/meabs/experiments, 2026-10-planted-errors/results (qwen3.8:27b Q4_K_M via Ollama, 144 GSM8K problems)."


def right(c, r):
    return c is not None and c.get("answer") == r["answer"]


def share(pairs):
    pairs = list(pairs)
    return 100 * sum(pairs) / len(pairs), sum(pairs), len(pairs)


cuts = [("No thinking", share(right(r["cut0"], r) for r in R)),
        ("Cut before\nfirst step", share(right(r["early"]["cut"], r) for r in R if r.get("early", {}).get("located"))),
        ("Cut before\nsecond-to-last", share(right(r["late"]["cut"], r) for r in R if r.get("late", {}).get("located"))),
        ("Full thinking", share(right(r.get("cutfull"), r) for r in R))]


def outcome(r, p):
    x = r[p]; a = x["planted"].get("answer"); t = x["planted"]["text"]
    if a == x["follow"]:
        return "follow"
    if a != r["answer"]:
        return "other"
    nums = NUMS.findall(t.split("</think>")[0])
    return "reply" if nums and float(nums[-1].replace(",", "")) == x["follow"] else "thinking"


KINDS = [("follow", "Followed the error to a wrong answer", NAVY), ("thinking", "Caught it in the thinking", TEAL),
         ("reply", "Thinking ended wrong; reply fixed it silently", BEIGE), ("other", "Other", PALE)]
counts = {}
for p in ("early", "late"):
    oc = [outcome(r, p) for r in R if right(r["free"], r) and r.get(p, {}).get("located")]
    counts[p] = {k: oc.count(k) for k, _, _ in KINDS}

plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.edgecolor": NAVY, "font.size": 13})
fig = plt.figure(figsize=(9, 4.6), dpi=200)
fig.suptitle("The thinking builds the answer, and a planted error often goes through", x=0.01, ha="left", fontsize=14.5, y=0.96)
a1 = fig.add_axes([0.06, 0.2, 0.36, 0.6]); a2 = fig.add_axes([0.55, 0.42, 0.38, 0.38])

for i, (name, (pc, k, n)) in enumerate(cuts):
    a1.bar(i, pc, width=0.62, color=TEAL if i == 3 else MID)
    a1.text(i, pc + 2, f"{pc:.0f}%", ha="center", fontsize=10)
a1.set_xticks(range(4), [c[0] for c in cuts], fontsize=8.5)
a1.set_ylim(0, 105); a1.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"], fontsize=9)
a1.set_title("Right when forced to answer", fontsize=11, loc="left")
a1.grid(axis="y", color=GRID); a1.set_axisbelow(True); a1.tick_params(axis="x", length=0)

for y, p, label in ((1, "early", "Error at\nfirst step"), (0, "late", "Error at\nsecond-to-last")):
    left = 0; n = sum(counts[p].values())
    for k, _, c in KINDS:
        w = 100 * counts[p][k] / n
        a2.barh(y, w, left=left, height=0.6, color=c, edgecolor="white", lw=1.5)
        if counts[p][k] >= 5:
            a2.text(left + w / 2, y, str(counts[p][k]), ha="center", va="center", fontsize=10,
                    color="white" if c in (NAVY, TEAL) else NAVY)
        left += w
    a2.text(101, y, f"of {n}", va="center", fontsize=9, color=MUTED)
a2.set_yticks([1, 0], ["Error at\nfirst step", "Error at\nsecond-to-last"], fontsize=9)
a2.set_xlim(0, 100); a2.set_xticks([0, 50, 100], ["0%", "50%", "100%"], fontsize=9)
a2.set_title("What happened to a planted wrong number", fontsize=11, loc="left")
a2.tick_params(axis="y", length=0)
for ax in (a1, a2):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in KINDS], labels=[l for _, l, _ in KINDS],
           loc="upper left", bbox_to_anchor=(0.54, 0.32), ncol=1, frameon=False, fontsize=9)
fig.text(0.01, 0.02, SOURCE, fontsize=8, color=MUTED)
fig.savefig(os.path.join(OUT, "chart-pe-planted.png"), facecolor="white")
print(os.path.join(OUT, "chart-pe-planted.png"), counts)
