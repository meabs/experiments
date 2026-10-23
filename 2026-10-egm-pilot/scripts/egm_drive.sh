#!/usr/bin/env bash
# Drives one EGM run turn by turn, so a person (here: Claude, acting as the human approver) can answer EGM's gates.
# It mirrors the rig's set-up: a fresh clone at 6a4a0a6 with one commit (setup.sh), Codex gpt-5.6-luna at low effort,
# a clean home (a per-run copy of home-egm, so runs cannot read each other's sessions), and a sandbox-exec profile that
# hides the experiments folder, the whole work folder except this run (reference clones, other runs) and the user's
# own agent folders.
#
# Usage:
#   egm_drive.sh start <run> <task> <prompt file>   new session in a fresh clone; prints the agent's last message
#   egm_drive.sh say   <run> <message file>         resumes the session with the approver's message
#   egm_drive.sh new   <run> <prompt file>          a second, fresh session in the same clone (the build step)
#   egm_drive.sh seed  <run> <task> <design file>   a fresh clone with an approved design at its root, for a build alone
#   egm_drive.sh grade <run>                        runs verify.sh (relevance check, hidden tests, full suite)
# Every turn's JSON events are kept in <run>/turns/NN.jsonl, and every message sent in <run>/turns/NN.in.md.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${EGM_WORK:-$HOME/code/benchmark/skills-impact-work}"
CMD="$1"; RUN="$2"; R="$W/egm-runs/$RUN"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
P="/opt/homebrew/opt/openjdk@21/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ARGS=(--skip-git-repo-check --json -m gpt-5.6-luna -c 'model_reasoning_effort="low"')
# EGM_HOME_SRC picks the Codex home copied into each run (default home-egm; home-clean has no plugin).
# Extra Codex arguments, e.g. EGM_ARGS="--enable multi_agent_v2" (recorded in <run>/args).
read -r -a EXTRA <<< "${EGM_ARGS:-}"
ARGS+=(${EXTRA[@]+"${EXTRA[@]}"})

profile() {
  cat > "$R/isolate.sb" <<EOF
(version 1)
(allow default)
(deny file-read* file-write* (subpath "$HOME/.agents") (subpath "$HOME/.claude") (subpath "$HOME/.codex") (subpath "$HOME/.cursor") (subpath "$HOME/code/experiments") (subpath "$W") (subpath "/private/tmp/claude-501"))
(allow file-read* file-write* (subpath "$R"))
(deny file-write* (subpath "$HOME/.m2/repository/com/shopizer"))
EOF
  # As the rig does: allow looking up (not listing) each folder above the run, so paths inside it resolve.
  local d="$R" lits=""
  while [ "$d" != "/" ]; do d="$(dirname "$d")"; lits="$lits (literal \"$d\")"; done
  echo "(allow file-read-metadata$lits)" >> "$R/isolate.sb"
}

turn() {  # turn <input file> <codex exec args...>
  local n; n=$(printf '%02d' $(( $(ls "$R/turns" | grep -c '\.jsonl$' || true) + 1 )))
  cp "$1" "$R/turns/$n.in.md"; shift
  printf '%s\n' "${EGM_ARGS:-}" > "$R/turns/$n.args"
  local t0; t0=$(date +%s)
  ( cd "$R/repo" && env -i HOME="$R/home" CODEX_HOME="$R/home/.codex" JAVA_HOME="$JAVA_HOME" PATH="$P" TERM=dumb \
      sandbox-exec -f "$R/isolate.sb" codex exec "$@" < /dev/null > "$R/turns/$n.jsonl" 2> "$R/turns/$n.err" ) || true
  echo $(( $(date +%s) - t0 )) > "$R/turns/$n.seconds"
  python3 -I - "$R/turns/$n.jsonl" "$R" <<'PY'
import json, sys
f, r = sys.argv[1], sys.argv[2]
last, tid, usage = "", None, None
for line in open(f):
    try: e = json.loads(line)
    except ValueError: continue
    if e.get("type") == "thread.started": tid = e.get("thread_id")
    it = e.get("item") or {}
    if e.get("type") == "item.completed" and it.get("type") == "agent_message": last = it.get("text", "")
    if e.get("type") == "turn.completed": usage = e.get("usage")
if tid: open(r + "/thread", "w").write(tid)
print(last)
print("\n[usage]", json.dumps(usage))
PY
}

case "$CMD" in
  start)
    rm -rf "$R"; mkdir -p "$R/turns"; echo "$3" > "$R/task"
    git clone -q "$W/shopizer" "$R/repo"; git -C "$R/repo" checkout -q 6a4a0a6
    ( cd "$R/repo" && TRIAL_QUESTION="$3" bash "$E/scripts/setup.sh" )
    cp -R "$W/${EGM_HOME_SRC:-home-egm}" "$R/home"
    profile
    turn "$4" -s danger-full-access "${ARGS[@]}" "$(cat "$4")" ;;
  seed)  # seed <run> <task> <design file>: a fresh clone with an approved design at its root, no turn run
    rm -rf "$R"; mkdir -p "$R/turns"; echo "$3" > "$R/task"
    git clone -q "$W/shopizer" "$R/repo"; git -C "$R/repo" checkout -q 6a4a0a6
    ( cd "$R/repo" && TRIAL_QUESTION="$3" bash "$E/scripts/setup.sh" )
    cp "$4" "$R/repo/design_draft.md"
    cp -R "$W/${EGM_HOME_SRC:-home-egm}" "$R/home"
    profile ;;
  say)
    turn "$3" resume -c 'sandbox_mode="danger-full-access"' "${ARGS[@]}" "$(cat "$R/thread")" "$(cat "$3")" ;;
  new)
    turn "$3" -s danger-full-access "${ARGS[@]}" "$(cat "$3")" ;;
  grade)
    T="$(cat "$R/task")"
    ( cd "$R/repo" && TRIAL_OUT="$R/grade" TRIAL_QUESTION="$T" TRIAL_ARM=egm TRIAL_AGENT=codex TRIAL_REP=1 \
        bash "$E/scripts/verify.sh" ) || echo "verify exit $?"
    cat "$R/grade/runs/$T/egm/codex/1/verify-summary.json" ;;
  *) echo "unknown command $CMD" >&2; exit 2 ;;
esac
