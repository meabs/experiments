"""Reads surefire reports in the clone after `mvn -Dmaven.test.failure.ignore=true clean test` and writes verify-summary.json.

Pass = the reactor compiled and ran, the hidden tests ran and passed, and no other test (existing or agent-added) failed."""
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

out, mvn_rc = sys.argv[1], int(sys.argv[2])
hidden_run = hidden_bad = other_bad = 0
failing = []
for f in glob.glob("**/target/surefire-reports/TEST-*.xml", recursive=True):
    try:
        s = ET.parse(f).getroot()
    except ET.ParseError:
        continue
    name, tests = s.get("name", f), int(s.get("tests", 0))
    bad = int(s.get("failures", 0)) + int(s.get("errors", 0))
    if ".hidden." in name:
        hidden_run += tests
        hidden_bad += bad
    elif bad:
        other_bad += bad
        failing.append(name)
summary = {"mvn_exit": mvn_rc, "hidden_tests": hidden_run, "hidden_pass": hidden_run > 0 and hidden_bad == 0,
           "other_failures": other_bad, "failing_suites": failing}
summary["pass"] = mvn_rc == 0 and summary["hidden_pass"] and other_bad == 0
json.dump(summary, open(os.path.join(out, "verify-summary.json"), "w"), indent=1)
print(json.dumps(summary))
sys.exit(0 if summary["pass"] else 1)
