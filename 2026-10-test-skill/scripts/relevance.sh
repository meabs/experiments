#!/usr/bin/env bash
# Does the agent's own test check its change? Run in the agent's clone (HEAD = the original code, the working tree = the
# agent's change). Usage: relevance.sh <out.json> [log dir]
#
# 1. Finds the test files the agent added or changed (under src/test, outside the hidden tests).
# 2. Runs the test classes among them with the agent's change.
# 3. Exports the original code (HEAD) to a temporary folder, copies the agent's test files in, and runs them again.
# A run has a relevant test if every one of its tests passes with the change, and at least one fails (or does not
# compile) on the original. Used by the grader (all arms) and by the Stop-hook gate (arm F). Never reads the hidden tests.
set -uo pipefail
OUT="$1"; LOGS="${2:-$(dirname "$OUT")}"
mkdir -p "$LOGS" "$(dirname "$OUT")"
LOGS="$(cd "$LOGS" && pwd)"; OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
HERE="$(cd "$(dirname "$0")" && pwd)"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21 PATH=/opt/homebrew/opt/openjdk@21/bin:$PATH
MVN=(mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository" -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false)
mkdir -p "$LOGS"

git add -A -N . 2>/dev/null
files=$(git diff --name-only --diff-filter=AM -- '*/src/test/*' ':(exclude)*/hidden/*' ':(exclude)**/target/**')
testfiles() { for f in $files; do [ "${f%.java}" != "$f" ] && grep -qE "@Test([^A-Za-z]|$)" "$f" 2>/dev/null && echo "$f"; done; }
classes=$(testfiles | xargs -n1 basename 2>/dev/null | sed 's/\.java$//' | sort -u | paste -sd, -)
modules=$(testfiles | sed 's#/src/test/.*##' | sort -u | paste -sd, -)

run() {  # <dir> <log name>: runs the agent's test classes in <dir>, leaves surefire reports there
  ( cd "$1" && find . -path '*/target/surefire-reports' -type d -prune -exec rm -rf {} + 2>/dev/null
    "${MVN[@]}" -pl "$modules" -am -Dtest="$classes" test > "$LOGS/$2" 2>&1; echo $? > "$LOGS/$2.rc" )
}

if [ -z "$classes" ]; then
  python3 -I "$HERE/relevance.py" "$OUT" none "" "" "" "" "$files"
  exit 0
fi

run "$PWD" relevance-change.log
WITH="$PWD"
ORIG="$(mktemp -d "${TMPDIR:-/tmp}/relevance.XXXXXX")" || { echo "mktemp failed" >&2; }
echo "original copy at $ORIG" >&2
git archive HEAD | tar -x -C "$ORIG" || echo "export of the original failed" >&2
for f in $files; do mkdir -p "$ORIG/$(dirname "$f")"; cp "$f" "$ORIG/$f"; done
run "$ORIG" relevance-original.log
python3 -I "$HERE/relevance.py" "$OUT" "$classes" "$WITH" "$ORIG" "$LOGS" "$modules" "$files"
rm -rf "$ORIG"
