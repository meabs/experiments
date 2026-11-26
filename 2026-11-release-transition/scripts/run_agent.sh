#!/usr/bin/env bash
# One Codex run in bubblewrap (hosted gpt-5.6-luna, medium effort, danger-full-access inside the sandbox) in a work folder.
# Usage: run_agent.sh <work dir> <run dir> <trial id> <prompt file> <session out>
set -uo pipefail
W="$(cd "$1" && pwd)"; R="$(cd "$2" && pwd)"; ID="$3"; P="$4"; S="$5"
export TRIAL_OUT="$R" TRIAL_ID="$ID" CODEX_PROFILE=hosted
cd "$W"
start=$(date +%s)
timeout 1500 "$HOME/code/benchmark/local-setup/codex-bwrap.sh" exec -c 'model_reasoning_effort="medium"' -s danger-full-access \
  --skip-git-repo-check --json --model gpt-5.6-luna "$(cat "$P")" < /dev/null > "$S" 2> "$S.err"
echo "exit $? seconds $(( $(date +%s) - start ))" >> "$S.done"
# Codex rotates the refresh token when it refreshes. Copies made per run would each burn the shared login (the first main run
# died of `refresh_token_reused`), so a refreshed per-run login is written back to the real one (atomic rename, newer only).
python3 -I - "$R/agent-homes/$ID/.codex/auth.json" "$HOME/.codex/auth.json" <<'PY'
import json, os, sys
a, b = sys.argv[1:3]
try:
    x, y = json.load(open(a)), json.load(open(b))
    if x.get("last_refresh", "") > y.get("last_refresh", "") and x.get("tokens", {}).get("refresh_token"):
        t = b + ".tmp"; open(t, "w").write(json.dumps(x)); os.chmod(t, 0o600); os.replace(t, b)
except Exception:
    pass
PY
rm -f "$R/agent-homes/$ID/.codex/auth.json"; rm -rf "$R/agent-homes/$ID/.codex/plugins" "$R/agent-homes/$ID/.codex/cache"
