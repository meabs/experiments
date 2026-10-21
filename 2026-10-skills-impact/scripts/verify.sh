#!/usr/bin/env bash
# Independent check after the agent finishes. Saves the agent's diff, adds the hidden test, runs the whole
# reactor's tests offline. Exit 0 only if everything (existing tests + hidden test) passes.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21 PATH=/opt/homebrew/opt/openjdk@21/bin:$PATH
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R"
git add -A -N . 2>/dev/null
git diff -- . ':(exclude)*.dat' ':(exclude)**/target/**' > "$R/agent.diff"
git diff --numstat -- . ':(exclude)*.dat' ':(exclude)**/target/**' > "$R/agent.numstat"
case "$TRIAL_QUESTION" in
  BUG)   D=sm-core/src/test/java/com/salesmanager/test/hidden ;;
  FEAT|CROSS) D=sm-shop/src/test/java/com/salesmanager/test/shop/hidden ;;
esac
mkdir -p "$D" && cp "$E/hidden/$TRIAL_QUESTION/"*.java "$D/"
mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository" clean test > "$R/verify-mvn.log" 2>&1
rc=$?
grep -E "Tests run:.*Fail|<<< (FAIL|ERR)|BUILD|COMPILATION ERROR" "$R/verify-mvn.log" | tail -20
exit $rc
