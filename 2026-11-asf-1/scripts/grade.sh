#!/usr/bin/env bash
# Grades one delivered change with ELC's hidden-test runner, outside the sandbox.
# B and C: the PR's head compared with the base (6a4a0a6) is applied, uncommitted, to a clean clone of the base;
# A: pass a diff file instead of a PR number. Then ELC's verify.sh runs (compile check, diff, hidden tests).
# Usage: grade.sh TICKET ARM REP (PR_NUMBER | DIFF_FILE) [REPO]   REPO: meabs/asf-run-NNN for the run's own repository
set -euo pipefail
X="$(cd "$(dirname "$0")/.." && pwd)"
ELC="$X/../2026-11-evidence-led"
T=$1 ARM=$2 REP=$3 SRC=$4 REPO=${5:-meabs/asf-shopizer}
BASE=6a4a0a6
OUT="$X/results/${GRADE_SET:-smoke}"
W="$OUT/work/$T-$ARM-$REP"
rm -rf "$W"; mkdir -p "$OUT/work"
git clone -q "$HOME/code/benchmark/skills-impact-work/shopizer" "$W"
git -C "$W" checkout -q "$BASE"
if [[ "$SRC" =~ ^[0-9]+$ ]]; then
  git -C "$W" fetch -q "https://github.com/$REPO.git" "pull/$SRC/head"
  git -C "$W" diff --binary "$BASE" FETCH_HEAD > "$OUT/work/$T-$ARM-$REP.patch"
  git -C "$W" apply --binary "$OUT/work/$T-$ARM-$REP.patch"
else
  git -C "$W" apply --binary "$SRC"
fi
cd "$W"
TRIAL_OUT="$OUT" TRIAL_QUESTION="$T" TRIAL_ARM="$ARM" TRIAL_AGENT=codex TRIAL_REP="$REP" bash "$ELC/scripts/verify.sh"
