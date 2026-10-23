"""Audits an EGM run from its Codex session files: each thread (main or subagent), its tokens and estimated cost, and the
fork_turns of every subagent it spawned ("none" is a fresh-context Goldfish; "all" copies the whole conversation).

Usage: python3 -I audit_sessions.py <sessions dir>   (results/egmN/sessions; *.jsonl or *.jsonl.gz)
Cost at gpt-5.6-luna list prices, as in the other experiments: (uncached input * 0.20 + cached * 0.02 + output * 1.20) / 1e6.
"""
import glob, gzip, json, os, sys

rows, total_t, total_c = [], 0, 0.0
for f in glob.glob(os.path.join(sys.argv[1], "*.jsonl*")):
    meta = tok = None; spawns = []; start = None
    for line in (gzip.open(f, "rt") if f.endswith(".gz") else open(f)):
        e = json.loads(line); p = e.get("payload") or {}
        if e.get("type") == "session_meta":
            meta = p.get("source"); start = p.get("timestamp")
        if e.get("type") == "event_msg" and p.get("type") == "token_count" and p.get("info"):
            tok = p["info"]["total_token_usage"]
        if e.get("type") == "response_item" and p.get("type") == "function_call" and "spawn" in p.get("name", ""):
            a = json.loads(p.get("arguments")); spawns.append(f"{a.get('task_name')}:{a.get('fork_turns')}")
    sub = meta.get("subagent", {}).get("thread_spawn", {}) if isinstance(meta, dict) else {}
    t = tok["total_tokens"] if tok else 0
    c = ((tok["input_tokens"] - tok["cached_input_tokens"]) * 0.20 + tok["cached_input_tokens"] * 0.02
         + tok["output_tokens"] * 1.20) / 1e6 if tok else 0.0
    total_t += t; total_c += c
    rows.append((start or "", sub.get("agent_path") if sub else "main", t, c, spawns))
print("| started | thread | tokens | cost | spawned (task:fork_turns) |\n| --- | --- | --- | --- | --- |")
for s, name, t, c, sp in sorted(rows):
    print(f"| {s[11:19]} | {name} | {t / 1e6:.2f}M | ${c:.3f} | {', '.join(sp)} |")
print(f"\nTotal: {total_t / 1e6:.2f}M tokens, ${total_c:.3f}; {sum(1 for r in rows if r[1] != 'main')} subagent threads.")
