#!/usr/bin/env bash
# Main run. The FMEA (25 runs per arm) in 9 chunks of up to 3 repetitions (run in parallel by the rig), and the
# feature tickets (5 runs per arm) one repetition at a time after FMEA chunks 1, 3, 5, 7 and 9; within each step the
# three arms go in a rotating order (A B C, B C A, C A B, ...), so neither task type nor any arm gets a better hour.
# The rig skips repetitions already finished, so this can simply be run again after an interruption.
# Usage: run_all.sh [out dir, default results/main]
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$E/results/main}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
ARMS=(A B C)
step=0
run() { # kind arm reps
  echo "$(date -Is) $1-$2 reps $3 start" >> "$OUT/progress.log"
  (cd "$RIG" && uv run -q trialrig run "$E/trial-$1-$2.local.toml" --agent codex --reps "$3" --out "$OUT/$1-$2" >> "$OUT/$1-$2.log" 2>&1)
  echo "$(date -Is) $1-$2 reps $3 rig exit $?" >> "$OUT/progress.log"; }
rotate() { for i in 0 1 2; do echo "${ARMS[$(( (i + step) % 3 ))]}"; done; step=$((step + 1)); }
feat=0
for chunk in 1 2 3 4 5 6 7 8 9; do
  upto=$(( chunk * 3 < 25 ? chunk * 3 : 25 ))
  for a in $(rotate); do run fmea "$a" "$upto"; done
  if [ $((chunk % 2)) -eq 1 ]; then
    feat=$((feat + 1))
    for a in $(rotate); do run feat "$a" "$feat"; done
  fi
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
