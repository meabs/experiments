#!/usr/bin/env bash
# Main run: 6 briefs x 5 runs in each arm (60 runs), arms interleaved by brief so both arms run at similar times.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$E/results/main}"
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
for B in D1 D2 D3 D4 D5 D6; do for A in A B; do
  echo "$(date -Is) $A $B start" >> "$OUT/progress.log"
  (cd "$RIG" && uv run -q trialrig run "$E/trial-$A.local.toml" --agent codex --question "$B" --out "$OUT/$A" >> "$OUT/$A.log" 2>&1)
  echo "$(date -Is) $A $B rig exit $?" >> "$OUT/progress.log"
done; done
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
