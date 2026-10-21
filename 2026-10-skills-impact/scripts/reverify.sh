#!/usr/bin/env bash
# Re-runs the independent check for finished runs from their saved agent.diff, on a fresh planted clone.
# Usage: reverify.sh <results dir> <question> <arm> <agent> <rep>. Writes reverify.log and prints PASS or FAIL.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$1"; Q="$2"; A="$3"; G="$4"; N="$5"
R="$OUT/runs/$Q/$A/$G/$N"
W="$(mktemp -d)/c"
git clone -q /Users/garry/code/benchmark/skills-impact-work/shopizer "$W" && cd "$W" && git checkout -q 6a4a0a6
export TRIAL_QUESTION="$Q" TRIAL_ARM="$A" TRIAL_AGENT="$G" TRIAL_REP="$N" TRIAL_DIR="$W"
bash "$E/scripts/setup.sh"
cp "$R/agent.diff" "$R/agent.diff.orig" 2>/dev/null || true
git apply --allow-empty "$R/agent.diff.orig" || { echo "FAIL (diff does not apply)"; exit 2; }
export TRIAL_OUT="$(mktemp -d)"
bash "$E/scripts/verify.sh" > /dev/null 2>&1; rc=$?
cp "$TRIAL_OUT/runs/$Q/$A/$G/$N/verify-mvn.log" "$R/reverify-mvn.log"; cp "$TRIAL_OUT/runs/$Q/$A/$G/$N/verify-summary.json" "$R/reverify-summary.json"
rm -rf "$(dirname "$W")" "$TRIAL_OUT"
[ $rc -eq 0 ] && echo PASS || echo FAIL
