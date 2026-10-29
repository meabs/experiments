#!/usr/bin/env bash
# Runs sec-authz one repetition at a time, the four arms in a rotating order (rep 1: A B C D; rep 2: B C D A; ...).
# `--reps r` makes the rig run rep r only, since reps 1..r-1 are finished and skipped, so this can simply be run again
# after an interruption. Usage: run_all.sh <out dir> <reps> [trial prefix, default "trial"]
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:?out dir}"; REPS="${2:?reps}"; PRE="${3:-trial}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
ARMS=(A B C D)
for r in $(seq 1 "$REPS"); do
  for i in 0 1 2 3; do
    a="${ARMS[$(( (i + r - 1) % 4 ))]}"
    echo "$(date -Is) rep $r $a start" >> "$OUT/progress.log"
    (cd "$RIG" && uv run -q trialrig run "$E/$PRE-$a.local.toml" --agent codex --reps "$r" --out "$OUT/$a" >> "$OUT/$a.log" 2>&1)
    echo "$(date -Is) rep $r $a rig exit $?" >> "$OUT/progress.log"
  done
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
