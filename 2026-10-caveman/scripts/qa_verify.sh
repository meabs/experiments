#!/usr/bin/env bash
# Grades the QA task: ANSWER.md against the bytecode-derived truth (Experiment 3's SU questions).
# Exit 0 only if mean F1 >= 0.95. Writes verify-summary.json and copies ANSWER.md next to the run.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R"
git add -A -N . 2>/dev/null
git diff --numstat > "$R/agent.numstat"
[ -f ANSWER.md ] && cp ANSWER.md "$R/ANSWER.md"
python3 -I "$E/scripts/grade_qa.py" "$E/hidden/QA/truth.json" ANSWER.md "$R/verify-summary.json"
