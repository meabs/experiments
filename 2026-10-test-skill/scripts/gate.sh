#!/usr/bin/env bash
# Stop hook for arm F (gate). Codex runs it when the agent tries to finish, with a JSON event on stdin.
# It runs the relevance check (relevance.sh, never the hidden tests) in the agent's clone. If the change has no relevant
# test, it blocks the finish once and tells the agent the result. On the second stop (stop_hook_active true) it records
# the check again but always lets the agent finish, so a run is sent back at most once. If the check itself fails to run
# ("check error"), the agent is never blocked.
# Each check is saved in the clone's .git folder (gate-<n>.json and its Maven logs), which verify.sh copies to the run.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IN="$(cat)"
CWD="$(printf '%s' "$IN" | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["cwd"])')"
ACTIVE="$(printf '%s' "$IN" | python3 -I -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())')"
cd "$CWD" || { echo '{}'; exit 0; }
G="$(git rev-parse --absolute-git-dir)"
n=$(ls "$G"/gate-*.json 2>/dev/null | wc -l | tr -d ' '); n=$((n + 1))
start=$(date +%s)
mkdir -p "$G/gate-$n-logs"
bash "$HERE/relevance.sh" "$G/gate-$n.json" "$G/gate-$n-logs" > "$G/gate-$n-logs/relevance.out" 2>&1
python3 -I - "$G/gate-$n.json" "$ACTIVE" "$start" <<'EOF'
import json, sys, time
p, active, start = sys.argv[1], sys.argv[2] == "true", int(sys.argv[3])
try:
    v = json.load(open(p))
except Exception:
    v = {"relevant": False, "reason": "check error: no result"}
v["gate_seconds"] = int(time.time()) - start
v["stop_hook_active"] = active
reason = v.get("reason", "")
msg = None
if not v.get("relevant") and not active and not reason.startswith("check error"):
    if reason == "no test of its own":
        msg = ("Before you finish: no test of your own was found in your change. Add a test that checks your change "
               "through the API, and run it. It should fail without your change and pass with it.")
    elif reason.startswith("its tests fail with the change"):
        msg = "Before you finish: " + reason.replace("its tests", "your tests") + ". Make them pass."
    elif reason == "its tests also pass without the change":
        msg = ("Before you finish: your tests also pass on the original code, so none of them checks your change. "
               "Add a test that fails without your change and passes with it.")
    else:
        msg = "Before you finish: your tests did not compile or run with your change. Make them run and pass."
v["blocked"] = msg is not None
v["message"] = msg
json.dump(v, open(p, "w"), indent=1)
print(json.dumps({"decision": "block", "reason": msg}) if msg else "{}")
EOF
