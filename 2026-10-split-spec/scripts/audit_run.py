"""(split-spec: from swarm-tax, plus per-coder reads, files patched and timing, and planner edits outside .team/.)
Audits one run from its Codex session files (main thread and every subagent): tokens and cost of every thread, the
subagents the main thread spawned and their fork_turns, whether the main thread (the planner) edited files itself, each
reviewer's VERDICT line, any `mvn install`, and any path outside the run's clone that a command touched.

Subagent tokens are only in the session files, not in the rig's event stream (EGM pilot), so cost comes from here.
Cost at gpt-5.6-luna list prices, as in the other experiments: (uncached input * 0.20 + cached * 0.02 + output * 1.20) / 1e6.

Usage: python3 -I audit_run.py <codex home or sessions dir> <clone path> > sessions.json
"""
import glob, gzip, json, os, re, sys

EDIT = re.compile(r"\*\*\* Begin Patch|apply_patch|(^|[;&|]\s*)(sed -i|perl -pi|tee |cat >)|>\s*[\w./-]+\.(java|xml|properties)")
VERDICT = re.compile(r"VERDICT:\s*(APPROVE|CHANGES)")
PATCH = re.compile(r"\*\*\* (?:Add|Update|Delete) File: ([^\s\\\"']+)")
PART = re.compile(r"(?<!!)\.team/part-(\d)")
TASK = re.compile(r"(?<![!\w])TASK\.md")  # a mention excluded from a search (--glob '!TASK.md') is not a read
PATH = re.compile(r"(/home/[^\s'\"`;)]+|/tmp/[^\s'\"`;)]+)")


def opener(f):
    return gzip.open(f, "rt") if f.endswith(".gz") else open(f)


def thread(f):
    t = {"file": os.path.basename(f), "role": "main", "agent_path": None, "tokens": None, "spawns": [], "edits": 0,
         "commands": [], "messages": [], "last": None}
    for line in opener(f):
        e = json.loads(line); p = e.get("payload") or {}
        t["last"] = e.get("timestamp") or t["last"]
        if e.get("type") == "session_meta":
            sub = ((p.get("source") or {}) if isinstance(p.get("source"), dict) else {}).get("subagent", {}).get("thread_spawn")
            if sub:
                t["role"], t["agent_path"] = "subagent", sub.get("agent_path")
            t["started"] = p.get("timestamp")
        elif e.get("type") == "event_msg" and p.get("type") == "token_count" and p.get("info"):
            t["tokens"] = p["info"]["total_token_usage"]
        elif e.get("type") == "response_item" and p.get("type") in ("function_call", "custom_tool_call"):
            name, args = p.get("name", ""), p.get("arguments") or p.get("input") or ""
            if "spawn" in name:
                try:
                    a = json.loads(args)
                except ValueError:
                    a = {}
                t["spawns"].append({"task_name": a.get("task_name"), "fork_turns": a.get("fork_turns")})
            else:
                t["commands"].append(args)
                if EDIT.search(args):
                    t["edits"] += 1
        elif e.get("type") == "response_item" and p.get("type") == "message" and p.get("role") == "assistant":
            t["messages"].append("".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict)))
    return t


def cost(k):
    return ((k["input_tokens"] - k["cached_input_tokens"]) * 0.20 + k["cached_input_tokens"] * 0.02 + k["output_tokens"] * 1.20) / 1e6


def main(home, clone):
    files = sorted(glob.glob(os.path.join(home, "**", "*.jsonl*"), recursive=True))
    threads = [thread(f) for f in files]
    tot = {k: 0 for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")}
    for t in threads:
        for k in tot:
            tot[k] += (t["tokens"] or {}).get(k, 0)
    main_t = [t for t in threads if t["role"] == "main"]
    subs = [t for t in threads if t["role"] == "subagent"]
    verdicts = [m.group(1) for t in subs for msg in t["messages"][-1:] for m in [VERDICT.search(msg or "")] if m]
    cmds = [c for t in threads for c in t["commands"]]
    outside = sorted({p for c in cmds for p in PATH.findall(c)
                      if not p.startswith(clone) and not p.startswith(os.path.expanduser("~/.m2"))})
    out = {
        "threads": len(threads), "subagents": len(subs),
        "spawns": [s for t in main_t for s in t["spawns"]],
        "subagent_spawns": [s for t in subs for s in t["spawns"]],
        "planner_edits": sum(t["edits"] for t in main_t),
        "verdicts": verdicts, "final_verdict": verdicts[-1] if verdicts else None,
        "mvn_install": sum(1 for c in cmds if re.search(r"\bmvnw?\b[^\n]*\binstall\b", c)),
        "paths_outside_clone": outside,
        "planner_code_edits": sum(1 for t in main_t for c in t["commands"] if EDIT.search(c) and ".team/" not in c),
        "coders": [{"agent_path": t["agent_path"], "started": t.get("started"), "ended": t["last"],
                    "read_task_md": any(TASK.search(c) for c in t["commands"]),
                    "parts_read": sorted({m for c in t["commands"] for m in PART.findall(c)}),
                    "files_patched": sorted({os.path.relpath(m, clone) if m.startswith("/") else m
                                             for c in t["commands"] for m in PATCH.findall(c)})}
                   for t in subs if t["agent_path"] and "review" not in t["agent_path"]],
        "read_task_md": {r: any(TASK.search(c) for t in subs if t["agent_path"] and (("review" in t["agent_path"]) == (r == "reviewer"))
                                for c in t["commands"]) for r in ("coder", "reviewer")},
        "tokens": tot, "cost": round(cost(tot), 5),
        "per_thread": [{"role": t["role"], "agent_path": t["agent_path"], "tokens": (t["tokens"] or {}).get("total_tokens", 0),
                        "cost": round(cost(t["tokens"]), 5) if t["tokens"] else 0, "edits": t["edits"],
                        "spawns": t["spawns"]} for t in threads],
    }
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
