#!/usr/bin/env bash
# Tests that bite (H4): runs each BUG run's own test changes against the planted, unfixed code.
# Usage: bite.sh <runs dir> <out json>. Per run: bites (a test fails), no-bite (all pass), no-compile, or no-tests.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
RUNS="$1"; OUTJ="$2"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21 PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"
T="$(mktemp -d)"
git clone -q "${SHOPIZER:-$HOME/code/benchmark/skills-impact-work/shopizer}" "$T/base" && (cd "$T/base" && git checkout -q 6a4a0a6 && TRIAL_QUESTION=BUG bash "$E/scripts/setup.sh" >/dev/null)

one() {
  r="$1"; key="${r#$RUNS/}"; W="$T/$(echo "$key" | tr / _)"
  tests=$(cut -f3 "$r/agent.numstat" | grep '/src/test/.*\.java$')
  [ -z "$tests" ] && { echo "$key no-tests"; return; }
  cp -R "$T/base" "$W"
  (cd "$W" && git apply --include='*/src/test/*' "$r/agent.diff") || { echo "$key no-apply"; return; }
  mods=$(echo "$tests" | cut -d/ -f1 | sort -u | paste -sd, -)
  classes=$(echo "$tests" | xargs -n1 basename | sed 's/\.java$//' | paste -sd, -)
  (cd "$W" && mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository" -pl "$mods" -am -Dtest="$classes" \
     -Dsurefire.failIfNoSpecifiedTests=false test > "$r/bite-mvn.log" 2>&1); rc=$?
  if grep -q "COMPILATION ERROR" "$r/bite-mvn.log"; then v=no-compile
  elif [ $rc -ne 0 ] && grep -qE "Tests run: [0-9]+, (Failures: [1-9]|Failures: 0, Errors: [1-9])" "$r/bite-mvn.log"; then v=bites
  elif [ $rc -eq 0 ]; then v=no-bite
  else v=error; fi
  rm -rf "$W"; echo "$key $v"
}
export -f one; export T RUNS
ls -d "$RUNS"/BUG/*/*/* | xargs -P 3 -I{} bash -c 'one {}' | sort > "$T/res.txt"
python3 -I -c "import json,sys; print(json.dumps(dict(l.split() for l in open(sys.argv[1])), indent=1))" "$T/res.txt" > "$OUTJ"
cat "$T/res.txt"; rm -rf "$T"
