"""Turns a Claude approver's transcript into a public log: the messages it was given (with any context the harness
injected, such as <system-reminder> blocks, removed), each tool call it made, and each reply it sent back. The raw
transcript is not published because the harness injects account details into it.

Usage: python3 -I approver_log.py <approver transcript .jsonl>  > approver-log.md
"""
import json, re, sys

def clean(text):
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    return text.strip()

out = []
for line in open(sys.argv[1]):
    e = json.loads(line)
    msg = e.get("message") or {}
    content = msg.get("content")
    if e.get("type") == "user":
        texts = [content] if isinstance(content, str) else [c.get("text", "") for c in content or [] if c.get("type") == "text"]
        for t in texts:
            t = clean(t)
            if t:
                out.append("## Given to the approver\n\n" + t)
    elif e.get("type") == "assistant" and isinstance(content, list):
        for c in content:
            if c.get("type") != "tool_use":
                continue
            if c["name"] == "SubagentHandback":
                inp = c.get("input") or {}
                out.append("## Approver's reply\n\n" + clean(str(inp.get("report") or inp.get("message") or inp)))
            else:
                out.append(f"- tool call `{c['name']}`: `{json.dumps(c.get('input'))[:300]}`")
print("\n\n".join(out))
