#!/usr/bin/env bash
# Validates tickets before any measured run (README, section 4): for each ticket,
#   1. the hidden tests on unchanged Shopizer 6a4a0a6 (how many fail; the ones that pass guard existing behaviour);
#   2. the reference patch applied: every hidden test passes and the whole existing suite still passes.
# Usage: validate.sh <work clone of shopizer> TICKET [TICKET ...]. The clone is reset to 6a4a0a6 before and after.
# Writes results/validation/<TICKET>.json and prints one line per ticket. Never runs `mvn install`.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="$(cd "${1:?work clone}" && pwd)"; shift
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:$PATH
MVN=(mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository" -Dmaven.test.failure.ignore=true)
H=sm-shop/src/test/java/com/salesmanager/test/shop/hidden
OUT="$E/results/validation"; mkdir -p "$OUT"

reset() { (cd "$W" && git reset -q --hard && git checkout -q 6a4a0a6 && git clean -qfd -- sm-core-model sm-core sm-shop-model sm-shop sm-core-modules); }

summary() {  # <ticket> <phase>: counts from the surefire reports of the last run
  python3 -I - "$W" <<'PY'
import glob, sys, xml.etree.ElementTree as ET
w = sys.argv[1]; hid = [0, 0]; other = [0, 0]
for f in glob.glob(w + "/**/target/surefire-reports/TEST-*.xml", recursive=True):
    s = ET.parse(f).getroot(); n = int(s.get("tests", 0)) - int(s.get("skipped", 0))
    bad = int(s.get("failures", 0)) + int(s.get("errors", 0))
    t = hid if ".hidden." in s.get("name", "") else other
    t[0] += n; t[1] += bad
print(f"{hid[0]} {hid[1]} {other[0]} {other[1]}")
PY
}

for T in "$@"; do
  reset
  cp "$E/hidden/_support/"*.java "$W/$H/" 2>/dev/null || { mkdir -p "$W/$H"; cp "$E/hidden/_support/"*.java "$W/$H/"; }
  cp "$E/hidden/$T/"*.java "$W/$H/"
  (cd "$W" && "${MVN[@]}" clean test > "$OUT/$T-original.log" 2>&1)
  read -r on of oo oof <<< "$(summary)"
  (cd "$W" && git apply "$E/reference/$T.patch") || { echo "$T: reference patch does not apply"; continue; }
  (cd "$W" && "${MVN[@]}" clean test > "$OUT/$T-reference.log" 2>&1)
  read -r rn rf ro rof <<< "$(summary)"
  ok=$([ "$rf" = 0 ] && [ "$rof" = 0 ] && [ "$rn" -gt 0 ] && echo true || echo false)
  printf '{"ticket": "%s", "original": {"hidden_run": %s, "hidden_failing": %s, "existing_run": %s, "existing_failing": %s}, "reference": {"hidden_run": %s, "hidden_failing": %s, "existing_run": %s, "existing_failing": %s}, "valid": %s}\n' \
    "$T" "$on" "$of" "$oo" "$oof" "$rn" "$rf" "$ro" "$rof" "$ok" | tee "$OUT/$T.json"
  rm -rf "${W:?}/$H"
  (cd "$W" && git checkout -q sm-shop/files/store/DownlaodRepository.dat 2>/dev/null)
done
reset
