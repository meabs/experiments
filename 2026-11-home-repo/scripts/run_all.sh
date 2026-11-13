#!/usr/bin/env bash
# Runs HR-1 one repetition at a time, the six arms in a rotating order. Usage: run_all.sh <out dir> <reps> [trial prefix, default "trial"]
# `--reps r` makes the rig run rep r only (earlier reps are finished and skipped), so this can be rerun after an interruption.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:?out dir}"; REPS="${2:?reps}"; PRE="${3:-trial}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
ARMS=(${ARM_LIST:-A B C D E F})
for r in $(seq 1 "$REPS"); do
  for i in $(seq 0 $(( ${#ARMS[@]} - 1 ))); do
    a="${ARMS[$(( (i + r - 1) % ${#ARMS[@]} ))]}"
    echo "$(date -Is) rep $r $a start" >> "$OUT/progress.log"
    (cd "$RIG" && uv run -q trialrig run "$E/$PRE-$a.local.toml" --agent codex --reps "$r" --out "$OUT/$a" >> "$OUT/$a.log" 2>&1)
    echo "$(date -Is) rep $r $a rig exit $?" >> "$OUT/progress.log"
  done
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
