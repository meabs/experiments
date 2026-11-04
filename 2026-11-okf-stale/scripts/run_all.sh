#!/usr/bin/env bash
# Main run: 6 arms x 3 tickets x 8 repetitions. One repetition at a time for every arm, the arms in a rotating order
# (A B D E F V, then B D E F V A, ...), so no arm gets a better hour. The rig skips repetitions already finished, so
# this can simply be run again after an interruption.
# Usage: run_all.sh [out dir, default results/main]
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$E/results/main}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
ARMS=(A B D E F V)
for rep in 1 2 3 4 5 6 7 8; do
  for i in 0 1 2 3 4 5; do
    a="${ARMS[$(( (i + rep - 1) % 6 ))]}"
    echo "$(date -Is) feat-$a reps $rep start" >> "$OUT/progress.log"
    (cd "$RIG" && uv run -q trialrig run "$E/trial-feat-$a.local.toml" --agent codex --reps "$rep" --out "$OUT/feat-$a" >> "$OUT/feat-$a.log" 2>&1)
    echo "$(date -Is) feat-$a reps $rep rig exit $?" >> "$OUT/progress.log"
  done
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
