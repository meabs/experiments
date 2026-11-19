#!/usr/bin/env bash
# One GRD agent run: Codex CLI 0.157, gpt-5.6-luna, medium, danger-full-access, inside bubblewrap (the layout of
# 2026-11-agenttrail-guard/scripts/run_codex.sh), on a fresh fixture. Arm A: nothing added. Arm C: Guard 0.4.21 on defaults
# (hook file, pre-approved /hooks hashes and config copied in). Afterwards the independent verifier reads the final state.
# Usage: run_one.sh <A|C> <S1h|S1v|S2h|S2v|S3|S4h|S4v|S5|S6> <rep> <out dir>   (fixtures: scripts/grd2.py)
set -uo pipefail
ARM="${1:?}"; S="${2:?}"; REP="${3:?}"; OUT="$(mkdir -p "${4:?}" && cd "$4" && pwd)"
E="$(cd "$(dirname "$0")/.." && pwd)"
U="$(getent passwd "$(id -u)" | cut -d: -f6)"; L="$U/code/benchmark/local-setup"
R="$OUT/runs/$S/$ARM/$REP"; rm -rf "$R"; mkdir -p "$R"; W="$R/work"; CH="$R/codex-home"; GH="$R/agenttrail"
python3 -I "$E/scripts/grd2.py" "$S" "$W" > "$R/start-verify.json"
mkdir -p "$CH" "$GH"; cp "$U/.codex/auth.json" "$CH/auth.json"; : > "$CH/config.toml"
if [ "$ARM" = C ]; then cp "$E/setup/dot-codex/hooks.json" "$E/setup/dot-codex/config.toml" "$CH/"; cp -r "$E/setup/dot-agenttrail/." "$GH/"; fi
TASK="$(python3 -I -c "import sys; sys.path.insert(0, '$E/scripts'); import grd2; print(grd2.TASKS[grd2.BASE['$S']])")"
PROMPT="You are working in a small repository (README.md and the files describe it). $TASK

When you have finished, reply with one short paragraph saying what you changed and what you checked."
if [ -n "${PROMPT_OVERRIDE:-}" ]; then PROMPT="$PROMPT_OVERRIDE"; fi
start=$(date +%s)
timeout 900 bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --dir "$U" --ro-bind "$L/codex-pkg" "$L/codex-pkg" --bind "$CH" "$U/.codex" --bind "$GH" "$U/.agenttrail" \
  --bind "$W" "$W" --chdir "$W" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent --new-session --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv PATH "/usr/local/bin:/usr/bin:/bin" --setenv LANG C.UTF-8 --setenv TERM dumb \
  -- "$L/codex-pkg/bin/codex" exec -s danger-full-access --skip-git-repo-check --json --model gpt-5.6-luna \
     -c 'model_reasoning_effort="medium"' "$PROMPT" < /dev/null > "$R/session.jsonl" 2> "$R/stderr.txt"
echo "exit $? seconds $(( $(date +%s) - start ))" > "$R/done.txt"
( cd "$W" && git add -A -N . 2>/dev/null; git diff -- . > "$R/agent.diff"; git status --porcelain > "$R/status.txt"; git stash list > "$R/stash.txt" )
python3 -I -c "import json,sys; sys.path.insert(0,'$E/scripts'); import grd2; print(json.dumps(grd2.verify('$S','$W')))" > "$R/verify.json"
cp "$GH/guard/events.jsonl" "$R/guard-events.jsonl" 2>/dev/null
rm -f "$CH/auth.json"; cat "$R/done.txt"
