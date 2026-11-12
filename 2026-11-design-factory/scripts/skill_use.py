"""Did the factory agents actually use the factory? Reads each run's Codex session log and records which factory
files the agent opened, which tools it ran and which design files it wrote. Plain runs are checked the same way
(they have no factory files, so anything found would be a leak). Usage: python3 skill_use.py results/main"""
import json, re, sys, glob, pathlib, collections
stage = pathlib.Path(sys.argv[1])
SK = ["brief-intake","design-research","journey-storyboard","visual-direction","prototype-build","design-critique",
      "content-design","accessibility-review","legal-review","banking-design","frontend-handoff","impeccable"]
TOOLS = ["contrast.py","lint_prototype.py","render_check.py","check_bundle.py"]
out = {}
for home in sorted(stage.glob("*/agent-homes/*")):
    m = re.match(r"d(\d)_([ab])_codex_(\d)", home.name)
    if not m: continue
    run = f"D{m[1]}/{m[2].upper()}/{m[3]}"
    logs = list(home.glob(".codex/sessions/**/rollout-*.jsonl"))
    reads, writes, tools, search = set(), set(), set(), 0
    for lg in logs:
        for l in open(lg):
            r = json.loads(l); p = r.get("payload", {})
            if p.get("type") != "custom_tool_call": continue
            t = p.get("input", "")
            if "web__run" in t: search += 1
            if "*** Begin Patch" in t:
                for w in re.findall(r"\*\*\* (?:Add|Update) File: (\S+)", t.replace("\\n", "\n")):
                    writes.add(w.split("/codex/")[-1] if "/codex/" in w else w)
                continue
            for s in SK:
                if f"skills/{s}/" in t: reads.add("skill:" + s)
            for x in re.findall(r"skills/impeccable/reference/([a-z\-]+)\.md", t): reads.add("impeccable-ref:" + x)
            if "okf/index.md" in t: reads.add("okf/index.md")
            if "okf/workflow.md" in t: reads.add("okf/workflow.md")
            for x in re.findall(r"okf/(rules|knowledge/\w+|industry/banking)/", t): reads.add("okf/" + x)
            for x in TOOLS:
                if f"tools/{x}" in t: tools.add(x)
    out[run] = {"reads": sorted(reads), "tools": sorted(tools), "writes": sorted(writes), "searches": search}
json.dump(out, open(stage / "skill-use.json", "w"), indent=1)
arms = {"A": [], "B": []}
for k, v in out.items(): arms[k.split("/")[1]].append(v)
def pct(arm, f): return f"{sum(1 for v in arms[arm] if f(v))}/{len(arms[arm])}"
L = ["| What | Plain | Factory |", "| --- | --- | --- |"]
L.append(f"| Opened okf/index.md | {pct('A', lambda v:'okf/index.md' in v['reads'])} | {pct('B', lambda v:'okf/index.md' in v['reads'])} |")
L.append(f"| Opened okf/workflow.md | {pct('A', lambda v:'okf/workflow.md' in v['reads'])} | {pct('B', lambda v:'okf/workflow.md' in v['reads'])} |")
for s in SK: L.append(f"| Opened skill {s} | {pct('A', lambda v:'skill:'+s in v['reads'])} | {pct('B', lambda v:'skill:'+s in v['reads'])} |")
L.append(f"| Opened banking industry pack | {pct('A', lambda v:'okf/industry/banking' in v['reads'])} | {pct('B', lambda v:'okf/industry/banking' in v['reads'])} |")
L.append(f"| Opened Impeccable reference files (any) | {pct('A', lambda v:any(r.startswith('impeccable-ref') for r in v['reads']))} | {pct('B', lambda v:any(r.startswith('impeccable-ref') for r in v['reads']))} |")
for t in TOOLS: L.append(f"| Ran tools/{t} | {pct('A', lambda v:t in v['tools'])} | {pct('B', lambda v:t in v['tools'])} |")
for n in ["01-brief","02-research","03-storyboard","04-direction","05-review","06-handoff"]:
    L.append(f"| Wrote design/{n}.md | {pct('A', lambda v:any(n in w for w in v['writes']))} | {pct('B', lambda v:any(n in w for w in v['writes']))} |")
L.append(f"| Used web search | {pct('A', lambda v:v['searches']>0)} | {pct('B', lambda v:v['searches']>0)} |")
(stage / "skill-use.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
