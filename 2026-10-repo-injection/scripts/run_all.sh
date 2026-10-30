#!/usr/bin/env bash
# Runs repo-injection one repetition at a time, the two arms in alternating order (rep 1: A B; rep 2: B A; ...), with
# the listener (the attacker's server) running throughout and logging to <out>/listener.jsonl.
# `--reps r` makes the rig run rep r only, since reps 1..r-1 are finished and skipped, so this can simply be run again
# after an interruption. Usage: run_all.sh <out dir> <reps> [trial prefix, default "trial"]
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:?out dir}"; REPS="${2:?reps}"; PRE="${3:-trial}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
if ss -ltn | grep -q '127.0.0.1:8088 '; then echo "port 8088 busy" >&2; exit 1; fi
python3 -I "$E/scripts/listener.py" "$OUT/listener.jsonl" &
LP=$!
trap 'kill $LP 2>/dev/null' EXIT
sleep 1
ARMS=(A B)
for r in $(seq 1 "$REPS"); do
  for i in 0 1; do
    a="${ARMS[$(( (i + r - 1) % 2 ))]}"
    [ -f "$E/$PRE-$a.local.toml" ] || continue
    echo "$(date -Is) rep $r $a start" >> "$OUT/progress.log"
    (cd "$RIG" && uv run -q trialrig run "$E/$PRE-$a.local.toml" --agent codex --reps "$r" --out "$OUT/$a" >> "$OUT/$a.log" 2>&1)
    echo "$(date -Is) rep $r $a rig exit $?" >> "$OUT/progress.log"
  done
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
