#!/usr/bin/env bash
# Pilot (README "Pilot"): arm A on every feature task twice, arm B once; the FMEA three times in A and in B.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$E/results/pilot}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
run() { echo "$(date -Is) $1 reps $2 start" >> "$OUT/progress.log"
  (cd "$RIG" && uv run -q trialrig run "$E/trial-pilot-$1.local.toml" --agent codex --reps "$2" --out "$OUT/$1" >> "$OUT/$1.log" 2>&1)
  echo "$(date -Is) $1 rig exit $?" >> "$OUT/progress.log"; }
run fmea-A 3
run fmea-B 3
run feat-A 2
run feat-B 1
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
