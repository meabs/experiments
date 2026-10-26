#!/usr/bin/env bash
# Independent check after the agent finishes (split-spec; from swarm-tax, plus the part files kept) (test-skill's Linux grader, copied here with relevance.sh, relevance.py and
# summarize.py, with this experiment's hidden tests):
# 1. visible check, for best-of-k selection (README, "Matching the spend"): does the change compile, before any hidden
#    test is present? -> visible.json {"compiles": bool}. Whether the agent's own tests pass comes from relevance.json.
# 2. the agent's diff, and test-skill's relevance check on the agent's own tests;
# 3. the hidden tests added, and the whole reactor's tests run offline -> verify-summary.json (hidden test cases by name).
# Exit 0 only if everything (existing tests + hidden tests) passes. Never runs `mvn install`.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:$PATH
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R"
MVN=(mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository")
"${MVN[@]}" -q -DskipTests test-compile > "$R/visible-mvn.log" 2>&1
python3 -I -c "import json,sys; json.dump({'compiles': sys.argv[1] == '0'}, open(sys.argv[2], 'w'))" "$?" "$R/visible.json"
git add -A -N . 2>/dev/null
# The planner's part files (split arms) are kept beside the run and left out of the agent's diff.
if [ -d .team ]; then mkdir -p "$R/team-parts" && cp .team/*.md "$R/team-parts/" 2>/dev/null; fi
git diff -- . ':(exclude)*.dat' ':(exclude)**/target/**' ':(exclude).team/**' > "$R/agent.diff"
git diff --numstat -- . ':(exclude)*.dat' ':(exclude)**/target/**' ':(exclude).team/**' > "$R/agent.numstat"
bash "$E/scripts/relevance.sh" "$R/relevance.json" "$R/relevance-logs" > /dev/null 2>&1
D=sm-shop/src/test/java/com/salesmanager/test/shop/hidden
mkdir -p "$D" && cp "$E/hidden/$TRIAL_QUESTION/"*.java "$D/"
"${MVN[@]}" -Dmaven.test.failure.ignore=true clean test > "$R/verify-mvn.log" 2>&1
mrc=$?
n=$(cat "$E/hidden/$TRIAL_QUESTION/"*.java | grep -cE "@Test([^A-Za-z]|$)")
python3 -I "$E/scripts/summarize.py" "$R" "$mrc" "$n"
