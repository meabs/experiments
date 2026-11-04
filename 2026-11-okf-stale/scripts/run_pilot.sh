#!/usr/bin/env bash
# Pilot (README "Pilot"): arms B and E, 2 runs of each ticket.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$E/results/pilot}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
for a in B E; do
  echo "$(date -Is) feat-$a start" >> "$OUT/progress.log"
  (cd "$RIG" && uv run -q trialrig run "$E/trial-pilot-feat-$a.local.toml" --agent codex --reps 2 --out "$OUT/feat-$a" >> "$OUT/feat-$a.log" 2>&1)
  echo "$(date -Is) feat-$a rig exit $?" >> "$OUT/progress.log"
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
