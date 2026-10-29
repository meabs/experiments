#!/usr/bin/env bash
# Independent check after the agent finishes (runs in the run's folder, outside the sandbox):
# 1. the agent's diff (agent.diff, agent.numstat) and the files it changed that the grader replaces with its own
#    copies (protected.txt: test support, existing tests, pom.xml);
# 2. scripts/grade.py: hidden tests plus the existing suite on a copy of the workspace -> grade.json.
# Exit 0 only if the build works and every hidden and existing test passes.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R"
git add -A -N . 2>/dev/null
git diff -- . ':(exclude)target/**' > "$R/agent.diff"
git diff --numstat -- . ':(exclude)target/**' > "$R/agent.numstat"
git diff --name-only -- pom.xml src/test/java/com/example/accounts/support src/test/resources \
  src/test/java/com/example/accounts/AccountApiTest.java src/test/java/com/example/accounts/CaseApiTest.java \
  src/test/java/com/example/accounts/ClosureApiTest.java src/test/java/com/example/accounts/AdminCustomerApiTest.java \
  > "$R/protected.txt"
python3 -I "$E/scripts/grade.py" "$TRIAL_QUESTION" . > "$R/grade.json" 2> "$R/grade.err"
rc=$?
python3 -I -c "import json,sys; d=json.load(open(sys.argv[1])); print('grade', 'pass' if d['pass'] else 'fail', 'build', d['build'], 'F', d['functional'], 'A', d['allows'], 'D', d['denies'], 'regression', d['regression'])" "$R/grade.json" 2>/dev/null
[ $rc -eq 0 ] && echo ok
exit $rc
