#!/usr/bin/env bash
# Runs okf-local one repetition at a time, the three arms in a rotating order (rep 1: no_okf okf source; rep 2: okf
# source no_okf; ...), with APU power logged once a second. `--reps r` makes the rig run rep r only, since reps 1..r-1
# are finished and skipped, so this can simply be run again after an interruption.
# Usage: run_all.sh <out dir> <reps>
set -uo pipefail
N="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:?out dir}"; REPS="${2:?reps}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
bash "$N/setup/powerlog.sh" "$OUT/power.csv" & PL=$!
trap 'kill $PL 2>/dev/null' EXIT
ARMS=(no_okf okf source)
for r in $(seq 1 "$REPS"); do
  for i in 0 1 2; do
    a="${ARMS[$(( (i + r - 1) % 3 ))]}"
    echo "$(date -Is) rep $r $a start" >> "$OUT/progress.log"
    (cd "$RIG" && uv run trialrig run "$N/trial-$a.local.toml" --agent codex --reps "$r" --out "$OUT/$a" >> "$OUT/$a.log" 2>&1)
    echo "$(date -Is) rep $r $a rig exit $?" >> "$OUT/progress.log"
  done
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
