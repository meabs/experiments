"""Level 1 of GRD: what does Guard's rule engine decide on 66 hook payloads? No model. Reads level1/payloads.json (labels
frozen before the first run), feeds each as a Codex PreToolUse payload to the pinned hook (Guard 0.4.21, defaults) with a
scratch HOME, writes results/level1/results.json and prints the summary. Decision: deny (a block, or an ask, which Codex
turns into a block) = stop; a system message with no deny = warn; nothing = allow."""
import collections, json, os, shutil, subprocess, sys, tempfile
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
payloads = json.load(open(f"{E}/level1/payloads.json"))
out = []
for p in payloads:
    home = tempfile.mkdtemp()
    shutil.copytree(f"{E}/setup/dot-agenttrail", f"{home}/.agenttrail")
    ev = {"hook_event_name": "PreToolUse", "session_id": "s", "cwd": "/work", "tool_name": "Bash",
          "tool_input": {"command": p["command"]}, "tool_use_id": "t", "turn_id": "1", "transcript_path": None, "model": "x"}
    r = subprocess.run(["node", f"{home}/.agenttrail/guard/codex/guard-hook.mjs"], input=json.dumps(ev), capture_output=True,
                       text=True, env={"HOME": home, "PATH": os.environ["PATH"]}, timeout=30)
    raw = r.stdout.strip()
    dec, rule = "allow", None
    if raw:
        j = json.loads(raw)
        h = j.get("hookSpecificOutput", {})
        if h.get("permissionDecision") == "deny":
            dec = "stop"
            import re
            m = re.search(r"\(guardrail ([\w.\-]+)\)", h.get("permissionDecisionReason", ""))
            rule = m.group(1) if m else None
        else:
            dec = "warn"
    out.append(dict(p, decision=dec, rule=rule, exit=r.returncode, stderr=r.stderr.strip()[:200], raw=raw[:300]))
    shutil.rmtree(home)
json.dump(out, open(f"{E}/results/level1/results.json", "w"), indent=1)
by = collections.defaultdict(collections.Counter)
for o in out:
    by[o["kind"]][o["decision"]] += 1
print("kind        n  stop warn allow")
for k in ("canonical", "equivalent", "lookalike"):
    c = by[k]; print(f"{k:11} {sum(c.values()):2} {c['stop']:4} {c['warn']:4} {c['allow']:5}")
print("errors:", sum(1 for o in out if o["exit"] != 0 or o["stderr"]))
for o in out:
    wrong = (o["expect"] == "stop" and o["decision"] != "stop") or (o["expect"] == "allow" and o["decision"] != "allow")
    if wrong:
        print(f"{o['id']} {o['kind']:10} expected {o['expect']:5} got {o['decision']:5} {o['rule'] or ''}  {o['command']}")
