#!/usr/bin/env bash
# Pilot (README "Pilot"): the plain arm once on every brief; the factory arm once on D1 and D5 to prove the rig and
# measure cost. Pilot runs are not part of the measured results.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$E/results/pilot}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
run() { echo "$(date -Is) $1 start" >> "$OUT/progress.log"
  (cd "$RIG" && uv run -q trialrig run "$E/trial-pilot-$1.local.toml" --agent codex --reps 1 ${2:+--question $2} --out "$OUT/$1" >> "$OUT/$1.log" 2>&1)
  echo "$(date -Is) $1 rig exit $?" >> "$OUT/progress.log"; }
run A
run B D1,D5
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
