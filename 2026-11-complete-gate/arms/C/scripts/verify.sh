#!/usr/bin/env bash
# Runs the full test suite and counts the results from the Surefire reports, so the count doesn't depend on reading
# Maven's output. Exits non-zero if no test ran or any test failed.
set -uo pipefail
cd "$(dirname "$0")/.."
rm -rf target/surefire-reports
mvn -B -o test > target-verify.log 2>&1
code=$?
read -r run fail err skip < <(python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
t = f = e = s = 0
for p in glob.glob("target/surefire-reports/TEST-*.xml"):
    r = ET.parse(p).getroot()
    t += int(r.get("tests", 0)); f += int(r.get("failures", 0)); e += int(r.get("errors", 0)); s += int(r.get("skipped", 0))
print(t, f, e, s)
PY
)
tail -n 40 target-verify.log | grep -E "ERROR|FAIL|Tests run:|BUILD" || true
rm -f target-verify.log
echo "TESTS RUN $run, FAILED $fail, ERRORS $err, SKIPPED $skip"
if [ "$run" -eq 0 ]; then echo "verify: no tests ran"; exit 1; fi
if [ "$fail" -gt 0 ] || [ "$err" -gt 0 ] || [ "$code" -ne 0 ]; then echo "verify: FAILED"; exit 1; fi
echo "verify: OK"
