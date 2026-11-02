#!/usr/bin/env bash
# Runs the full test suite and counts the results from the Surefire reports, so the count doesn't depend on reading
# Maven's output. Also checks every class in tests/expected-tests.txt ran at least its listed number of tests.
# Exits non-zero if no test ran, any test failed, or an expected class is missing.
set -uo pipefail
cd "$(dirname "$0")/.."
rm -rf target/surefire-reports
mvn -B -o test > target-verify.log 2>&1
code=$?
tail -n 40 target-verify.log | grep -E "ERROR|FAIL|Tests run:|BUILD" || true
rm -f target-verify.log
python3 - "$code" <<'PY'
import glob, sys, xml.etree.ElementTree as ET
code = int(sys.argv[1])
t = f = e = s = 0
ran = {}
for p in glob.glob("target/surefire-reports/TEST-*.xml"):
    r = ET.parse(p).getroot()
    n = int(r.get("tests", 0)) - int(r.get("skipped", 0))
    t += int(r.get("tests", 0)); f += int(r.get("failures", 0)); e += int(r.get("errors", 0)); s += int(r.get("skipped", 0))
    cls = r.get("name", "").rsplit(".", 1)[-1]
    ran[cls] = ran.get(cls, 0) + n
expected = []
for line in open("tests/expected-tests.txt"):
    line = line.split("#", 1)[0].split()
    if len(line) == 2:
        expected.append((line[0], int(line[1])))
missing = [(c, ran.get(c, 0), m) for c, m in expected if ran.get(c, 0) < m]
print(f"TESTS RUN {t}, FAILED {f}, ERRORS {e}, SKIPPED {s}")
print(f"EXPECTED CLASSES {len(expected) - len(missing)} of {len(expected)} ran")
for c, r, m in missing:
    print(f"MISSING: {c} (ran {r} of at least {m})")
if t == 0:
    print("verify: no tests ran"); sys.exit(1)
if f or e or code:
    print("verify: FAILED"); sys.exit(1)
if missing:
    print("verify: FAILED, expected tests missing"); sys.exit(1)
print("verify: OK")
PY
