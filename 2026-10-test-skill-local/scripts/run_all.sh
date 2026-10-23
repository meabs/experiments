#!/usr/bin/env bash
# Runs the measured stages one after another on the local model, each with an APU power log in its own folder:
#   stage1 (arms A-D), stage1-medium (E), stage1-gate (F), stage1-stop (G). One run at a time (one GPU).
# A stage already finished is skipped by the rig (run.json present). After an interruption, run again with --retry-failed
# to rerun only runs that did not finish ok. Usage: run_all.sh <trials dir> [--retry-failed]
set -uo pipefail
N="$(cd "$(dirname "$0")/.." && pwd)"; T="$(cd "$N/.." && pwd)/2026-10-test-skill"
OUT="${1:?trials dir}"; shift || true
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"; SETUP="${SETUP:-$HOME/code/benchmark/local-setup}"
mkdir -p "$OUT"
for s in "stage1:$T/trial.local.toml" "stage1-medium:$T/trial-medium.local.toml" "stage1-gate:$T/trial-gate.local.toml" \
         "stage1-stop:$N/trial-stop.local.toml"; do
  name="${s%%:*}"; toml="${s#*:}"; d="$OUT/$name"; mkdir -p "$d"
  echo "$(date -Is) start $name ($toml)"
  "$SETUP/powerlog.sh" "$d/power.part.csv" & P=$!
  (cd "$RIG" && uv run trialrig run "$toml" --agent codex --out "$d" "$@")
  rc=$?; kill $P 2>/dev/null; wait $P 2>/dev/null
  # append this session's power samples to the stage's log (keeps earlier sessions after a restart)
  if [ -f "$d/power.csv" ]; then tail -n +2 "$d/power.part.csv" >> "$d/power.csv"; else mv "$d/power.part.csv" "$d/power.csv"; fi
  rm -f "$d/power.part.csv"
  echo "$(date -Is) end $name (rig exit $rc)"
done
