#!/usr/bin/env bash
# Independent check after the agent finishes (runs in the run's folder, outside the sandbox):
# 1. the agent's diff (agent.diff), and whether it changed the files that stand in for the server, network and browser
#    (protected.json);
# 2. the hidden tests (hidden/<task>.py, plain Playwright, independent of WebMCP Resilience) on a copy of the page with
#    those three files restored -> hidden.json (cases passed).
# Exit 0 only if the protected files are unchanged and every hidden case passes.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
X="${WEBMCP_WORK:-$HOME/code/benchmark/webmcp-exp}"
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R"
git add -A -N . 2>/dev/null
git diff -- . ':(exclude).webmcp/runs/**' > "$R/agent.diff"
git diff --numstat -- . ':(exclude).webmcp/runs/**' > "$R/agent.numstat"
changed=()
for f in api.js latency.js webmcp-host.js; do
  cmp -s "$f" "$E/apps/$TRIAL_QUESTION/$f" || changed+=("$f")
done
python3 -I -c "import json,sys; json.dump({'changed': sys.argv[2:]}, open(sys.argv[1], 'w'))" "$R/protected.json" "${changed[@]}"
T="$(mktemp -d)"
rsync -a --exclude .git --exclude .venv --exclude .webmcp ./ "$T/"
for f in api.js latency.js webmcp-host.js; do cp "$E/apps/$TRIAL_QUESTION/$f" "$T/$f"; done
m="${TRIAL_QUESTION//-/_}"
(cd "$E/hidden" && "$X/env-plain/bin/python" "$m.py" "$T") > "$R/hidden.json" 2> "$R/hidden.err"
hrc=$?
rm -rf "$T"
cat "$R/hidden.json" | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(f\"hidden {d['passed']}/{d['total']}\")" 2>/dev/null
[ ${#changed[@]} -eq 0 ] || { echo "verify: protected files changed: ${changed[*]}" >&2; exit 1; }
[ $hrc -eq 0 ] || { echo "verify: hidden tests failed" >&2; exit 1; }
echo ok
