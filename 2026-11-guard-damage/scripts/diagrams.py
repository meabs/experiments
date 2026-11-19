"""GRD diagrams (diagrams/*.html, SVG 1800 px wide); render to PNG with diagrams/render.sh. Reads results/level1,
results/level3 and results/main. Colours: the dataviz skill's categorical slots 1 to 5 in fixed order (blue #2a78d6,
orange #eb6834, aqua #1baf7a, yellow #eda100, magenta #e87ba4); `validate_palette.js` passes light mode (worst adjacent CVD
dE 9.1, normal-vision 19.6). Aqua, yellow and magenta sit below 3:1 on white, so every segment carries its count and name as
text (the relief rule). Usage: python3 -I scripts/diagrams.py"""
import collections, json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "diagrams"
SRC = "Source: github.com/meabs/experiments, 2026-11-guard-damage"
C = {1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a", 4: "#eda100", 5: "#e87ba4"}
GREY = "#c9c8c2"


def page(h, body):
    return (f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{h}" viewBox="0 0 1800 {h}">\n{body}</svg>\n')


def stacked(title, sub, rows, segs, note, src_note, x0=520, w=1170, unit="items"):
    """rows: [(label, {seg: count})]; segs: [(key, name, colour)]. Horizontal 100% bars, 2 px surface gap between fills."""
    s = [f'<text x="40" y="62" class="th">{title}</text>', f'<text x="40" y="102" class="ts">{sub}</text>']
    lx = 40
    for k, name, col in segs:  # legend, one row, in series order
        s.append(f'<rect x="{lx}" y="136" width="26" height="26" rx="5" fill="{col}"/><text x="{lx + 38}" y="158" class="t">{name}</text>')
        lx += 70 + 15 * len(name)
    y = 200
    for label, cnt in rows:
        tot = sum(cnt.get(k, 0) for k, _, _ in segs)
        s.append(f'<text x="40" y="{y + 40}" class="tb">{label}</text><text x="40" y="{y + 72}" class="tsm">{tot} {unit}</text>')
        x = x0
        for k, name, col in segs:
            n = cnt.get(k, 0)
            if not n:
                continue
            wd = w * n / tot
            s.append(f'<rect x="{x + 1:.1f}" y="{y}" width="{max(wd - 2, 1):.1f}" height="76" rx="6" fill="{col}"/>')
            if wd > 54:
                s.append(f'<text x="{x + wd / 2:.1f}" y="{y + 49}" text-anchor="middle" class="tw" style="fill:#0b0b0b">{n}</text>')
            x += wd
        y += 112
    s.append(f'<text x="40" y="{y + 20}" class="ts">{note}</text>')
    s.append(f'<text x="1760" y="{y + 70}" class="tsm" text-anchor="end">{SRC} ({src_note})</text>')
    return page(y + 90, "\n".join(s))


def level1():
    r = json.load(open(ROOT / "results/level1/results.json"))
    rows = []
    for k, label in (("canonical", "Textbook harmful command"), ("equivalent", "Same harm, another shape"), ("lookalike", "Harmless lookalike")):
        c = collections.Counter(x["decision"] for x in r if x["kind"] == k)
        rows.append((label, {"stop": c["stop"], "warn": c["warn"], "allow": c["allow"]}))
    return stacked("Guard stops the textbook command and misses other shapes of the same harm",
                   "What the rule engine decided on 66 hook payloads, no model. A stop is a block or an ask, which Codex turns into a block.",
                   rows, [("stop", "stopped", C[1]), ("warn", "warned", C[4]), ("allow", "allowed", GREY)],
                   "Harm shapes should be stopped; harmless lookalikes should be allowed. Labels were written before the run.",
                   "results/level1/results.json", )


def level3():
    r = json.load(open(ROOT / "results/level3/results.json"))["harm_routes"]
    names = {"S1": "S1  uncommitted work", "S2": "S2  customer database", "S3": "S3  tests", "S4": "S4  release archive", "S5": "S5  production config"}
    rows = []
    for s, label in names.items():
        c = collections.Counter(x["outcome"] for x in r if x["scenario"] == s)
        rows.append((label, {"a": c["stopped, no harm"], "c": c["NOT stopped, harm done"], "b": c["stopped, harm anyway"]}))
    return stacked("Most routes to the harm were not stopped, and one stop came too late",
                   "Scripted replay, no model: each route is run only if the hook allows it, then the final state is checked against the protected invariant.",
                   rows, [("a", "stopped, nothing lost", C[1]), ("c", "not stopped, harm done", C[2]), ("b", "stopped, harm anyway", C[3])],
                   "Routes: direct command, other command forms, a script, an interpreter, a shell write. 23 routes in all.",
                   "results/level3/results.json")


def level2():
    p = ROOT / "results/main/analysis.json"
    if not p.exists():
        return None
    a = json.load(open(p))["harm_set_by_arm"]
    order = [("no stop, safe", "no stop, safe", C[1]), ("stop, then safe recovery", "stopped, then recovered", C[2]),
             ("stop, then task not done", "stopped, task not done", C[3]), ("stop, then harm anyway", "stopped, harm anyway", C[4]),
             ("harm, no stop", "harm, no stop", C[5])]
    rows = [(f"{arm}  " + ("Codex defaults" if arm == "A" else "Codex + Guard"), a[arm]["outcomes"]) for arm in "AC"]
    return stacked("What happened in each run where a documented routine step was harmful",
                   "The four fixtures where the project's own docs contain a harmful step (uncommitted work, release archive; in a script or written out): 20 runs per arm.",
                   rows, order, "A stop is Guard's own log (arm C) or, for Codex's native rejection of rm -rf in arm A, the agent saying so.",
                   "results/main/analysis.json", unit="runs")


def level2_fixtures():
    p = ROOT / "results/main/analysis.json"
    if not p.exists():
        return None
    pf = json.load(open(p))["per_fixture"]
    names = {"S1v": "S1 visible command", "S1h": "S1 hidden script", "S4v": "S4 visible command", "S4h": "S4 hidden script"}
    rows = []
    for f, label in names.items():
        for arm, an in (("A", "Codex defaults"), ("C", "Codex + Guard")):
            h, n = pf[f][arm]["harm"], pf[f][arm]["n"]
            rows.append((f"{label}, {arm}", {"safe": n - h, "harm": h}))
    return stacked("Guard helped on one fixture, the visible git command, and on none of the other three",
                   "Runs that finished the task safely or lost the protected work, 5 runs per bar; A is Codex defaults, C adds Guard.",
                   rows, [("safe", "task done, nothing lost", C[1]), ("harm", "protected work lost", C[2])],
                   "S1: uncommitted work in the tree. S4: the release archive that cannot be rebuilt. The pre-registered test pools the four fixtures.",
                   "results/main/analysis.json", unit="runs")


for name, fn in (("1-recognition", level1), ("2-routes", level3), ("3-outcomes", level2), ("4-by-fixture", level2_fixtures)):
    html = fn()
    if html:
        (OUT / f"{name}.html").write_text(html)
        print("wrote", name)
