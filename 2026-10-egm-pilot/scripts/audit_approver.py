"""Audits a Claude approver's transcript: every tool call it made, and any that touched a path outside its run's clone
or used a tool that can change files. Prints one line per call and a verdict.

Usage: python3 -I audit_approver.py <approver transcript .jsonl> <run clone path>
"""
import json, re, sys

f, clone = sys.argv[1], sys.argv[2].rstrip("/")
calls, bad = 0, []
for line in open(f):
    e = json.loads(line)
    msg = e.get("message") or {}
    if e.get("type") != "assistant" or not isinstance(msg.get("content"), list):
        continue
    for c in msg["content"]:
        if c.get("type") != "tool_use":
            continue
        calls += 1
        name, inp = c.get("name"), json.dumps(c.get("input"))
        if name == "SubagentHandback":  # the reply text; paths in it are API paths, not files
            continue
        paths = re.findall(r"/(?:Users|private|tmp|var|opt|etc)[^\s\"'`)|;]*", inp)
        outside = [p for p in paths if not p.startswith(clone)]
        writes = name in ("Write", "Edit", "NotebookEdit")
        if name == "Bash":
            cmd = c["input"].get("command", "").replace("2>/dev/null", "")
            writes = writes or bool(re.search(r"(^|[;&|]\s*)(rm|mv|cp|sed -i|tee|git (commit|checkout|reset|apply)|mvn|\./mvnw)\b|>", cmd))
        print(f"{name}: {inp[:160]}")
        if outside or writes:
            bad.append((name, outside, writes))
print(f"\n{calls} tool calls; {len(bad)} outside the clone or writing: {bad}")
