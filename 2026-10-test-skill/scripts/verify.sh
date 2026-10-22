#!/usr/bin/env bash
# Independent check after the agent finishes. Saves the agent's diff, runs the relevance check on the agent's own tests
# (relevance.sh), saves the gate's records if any, then adds the hidden test and runs the whole reactor's tests offline.
# Exit 0 only if everything (existing tests + hidden test) passes.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21 PATH=/opt/homebrew/opt/openjdk@21/bin:$PATH
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R"
git add -A -N . 2>/dev/null
git diff -- . ':(exclude)*.dat' ':(exclude)**/target/**' > "$R/agent.diff"
git diff --numstat -- . ':(exclude)*.dat' ':(exclude)**/target/**' > "$R/agent.numstat"
bash "$E/scripts/relevance.sh" "$R/relevance.json" "$R/relevance-logs" > /dev/null 2>&1
G="$(git rev-parse --git-dir)"
for f in "$G"/gate-*; do [ -e "$f" ] && cp -R "$f" "$R/"; done
D=sm-shop/src/test/java/com/salesmanager/test/shop/hidden
mkdir -p "$D" && cp "$E/hidden/$TRIAL_QUESTION/"*.java "$D/"
mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository" -Dmaven.test.failure.ignore=true clean test > "$R/verify-mvn.log" 2>&1
mrc=$?
n=$(cat "$E/hidden/$TRIAL_QUESTION/"*.java | grep -cE "@Test([^A-Za-z]|$)")
python3 -I "$E/scripts/summarize.py" "$R" "$mrc" "$n"
