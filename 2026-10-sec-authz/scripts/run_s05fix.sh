#!/usr/bin/env bash
# Amendment 2026-10-29 rerun: S05, arms C and D, 10 reps, alternating which arm goes first.
set -uo pipefail
E=~/code/experiments/2026-10-sec-authz; OUT=~/code/benchmark/sec-authz-work/s05fix; RIG=~/code/benchmark/AgentTrialRig
mkdir -p "$OUT"
for r in $(seq 1 10); do
  if [ $((r % 2)) = 1 ]; then order="C D"; else order="D C"; fi
  for a in $order; do
    echo "$(date -Is) rep $r $a start" >> "$OUT/progress.log"
    (cd "$RIG" && uv run -q trialrig run "$E/trial-s05fix-$a.local.toml" --agent codex --reps "$r" --out "$OUT/$a" >> "$OUT/$a.log" 2>&1)
    echo "$(date -Is) rep $r $a rig exit $?" >> "$OUT/progress.log"
  done
done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
