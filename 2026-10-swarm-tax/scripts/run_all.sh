#!/usr/bin/env bash
# Runs the three trial files side by side (each 3 runs at a time), with a checksum of the shared Maven repository's
# com/shopizer before and after. A finished run is skipped by the rig, so this can be run again after an interruption
# (add --retry-failed to rerun runs that did not finish ok). Usage: run_all.sh <out dir> [rig args]
set -uo pipefail
N="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:?out dir}"; shift || true
RIG="${RIG:-$HOME/code/benchmark/AgentTrialRig}"
mkdir -p "$OUT"
m2() { (cd "$HOME/.m2/repository" && find com/shopizer -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum); }
echo "$(date -Is) m2 before: $(m2)" >> "$OUT/m2.log"
for a in solo team team-full; do
  (cd "$RIG" && uv run trialrig run "$N/trial-$a.local.toml" --agent codex --out "$OUT/$a" "$@" > "$OUT/$a.log" 2>&1
   echo "$(date -Is) $a rig exit $?" >> "$OUT/progress.log") &
done
wait
echo "$(date -Is) m2 after: $(m2)" >> "$OUT/m2.log"
echo "$(date -Is) ALL DONE" >> "$OUT/progress.log"
