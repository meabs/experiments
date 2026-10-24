"""Prints one recorded run's transcript (thinking, tool calls, tool results, final answer) and its score.
Usage: python3 -I src/show.py <results dir> <scenario>/<condition>/<seed>
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from score import score  # noqa: E402

D, key = sys.argv[1:3]
i, c, s = key.split("/")
r = next(r for r in map(json.loads, open(os.path.join(D, "runs.jsonl"))) if (r["scenario"], r["condition"], r["seed"]) == (i, c, int(s)))
for m in r["transcript"]:
    if m["role"] == "system":
        continue
    print(f"--- {m['role']}" + (f" ({m.get('tool_name')})" if m["role"] == "tool" else ""))
    if m.get("thinking"):
        print("[thinking]", m["thinking"])
    if m.get("tool_calls"):
        print("[tool calls]", json.dumps([t["function"] for t in m["tool_calls"]]))
    if m.get("content"):
        print(m["content"])
print("--- score")
print(json.dumps(score(r, json.load(open(os.path.join(ROOT, "scenarios", "ground_truth.json")))), indent=1))
