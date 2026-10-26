#!/usr/bin/env bash
# Validates a task's hidden tests: (1) on the original code, (2) the whole reactor's tests with the reference applied.
# Usage: validate.sh TASK   (reference worktree at swarm-dev/TASK). Writes swarm-dev/TASK.validate.txt
set -uo pipefail
T="$1"; D=~/code/benchmark/swarm-dev; E=~/code/experiments/2026-10-swarm-tax
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:$PATH
MVN=(mvn -o -B -Dmaven.repo.local=$HOME/.m2/repository)
H=sm-shop/src/test/java/com/salesmanager/test/shop/hidden
O="$D/orig-$T"; rm -rf "$O"; git -C "$D/base" worktree prune; git -C "$D/base" worktree add -q "$O" 6a4a0a6
mkdir -p "$O/$H" && cp "$E/hidden/$T/"*.java "$O/$H/"
cls=$(basename "$E/hidden/$T/"*.java .java)
(cd "$O" && "${MVN[@]}" -pl sm-shop -am -Dtest="$cls" -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false -Dmaven.test.failure.ignore=true test > "$D/$T.orig.log" 2>&1)
mkdir -p "$D/$T/$H" && cp "$E/hidden/$T/"*.java "$D/$T/$H/"
(cd "$D/$T" && "${MVN[@]}" -Dmaven.test.failure.ignore=true clean test > "$D/$T.ref.log" 2>&1)
{ echo "== original code: $(grep -E 'Tests run:.*in com.salesmanager.test.shop.hidden' "$D/$T.orig.log" || echo 'hidden test did not run (compile failure?)')"
  grep -E "^\[ERROR\] +[A-Za-z]+Test\.[a-zA-Z]+|COMPILATION ERROR" "$D/$T.orig.log" | head -40
  echo "== reference, whole reactor:"; grep -E "Tests run: [0-9]+, Failures: [0-9]+, Errors: [0-9]+, Skipped: [0-9]+$|BUILD|Tests run:.*hidden" "$D/$T.ref.log"
} > "$D/$T.validate.txt"
git -C "$D/base" worktree remove --force "$O"
echo "VALIDATED $T"
