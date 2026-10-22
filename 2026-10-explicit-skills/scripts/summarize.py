"""Reads surefire reports in the clone after `mvn -Dmaven.test.failure.ignore=true clean test` and writes verify-summary.json.

Pass = the reactor compiled and ran, the hidden tests ran and passed, and no other test (existing or agent-added) failed.

Usage: summarize.py <run dir> <mvn exit code> [expected hidden test count]. Hardened after stage 1 (see REPORT.md,
"Measurement defects"): a skipped hidden test, fewer hidden tests than expected, or an unreadable report fails the run.
An audit of all 162 stage-1 runs found none of these cases, so no recorded grade changes.

verify-vs-skills adds "cases": the outcome of each hidden test by name, so that `keeps...` (neighbour) tests can be
reported apart from target tests."""
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

out, mvn_rc = sys.argv[1], int(sys.argv[2])
expected = int(sys.argv[3]) if len(sys.argv) > 3 else None
hidden_run = hidden_bad = hidden_skipped = other_bad = 0
failing, unreadable = [], []
cases = {}
for f in glob.glob("**/target/surefire-reports/TEST-*.xml", recursive=True):
    try:
        s = ET.parse(f).getroot()
    except ET.ParseError:
        unreadable.append(f)
        continue
    name, tests = s.get("name", f), int(s.get("tests", 0))
    bad = int(s.get("failures", 0)) + int(s.get("errors", 0))
    if ".hidden." in name:
        hidden_run += tests
        hidden_bad += bad
        hidden_skipped += int(s.get("skipped", 0))
        for tc in s.iter("testcase"):
            cases[tc.get("name")] = ("fail" if tc.find("failure") is not None else "error" if tc.find("error") is not None
                                     else "skipped" if tc.find("skipped") is not None else "pass")
    elif bad:
        other_bad += bad
        failing.append(name)
hidden_ok = hidden_run > 0 and hidden_bad == 0 and hidden_skipped == 0 and (expected is None or hidden_run == expected)
summary = {"mvn_exit": mvn_rc, "hidden_tests": hidden_run, "hidden_pass": hidden_ok,
           "other_failures": other_bad, "failing_suites": failing, "cases": cases,
           "keeps_broken": any(o != "pass" for n, o in cases.items() if n.startswith("keeps"))}
if expected is not None:
    summary["hidden_expected"] = expected
if hidden_skipped:
    summary["hidden_skipped"] = hidden_skipped
if unreadable:
    summary["unreadable_reports"] = unreadable
summary["pass"] = mvn_rc == 0 and hidden_ok and other_bad == 0 and not unreadable
json.dump(summary, open(os.path.join(out, "verify-summary.json"), "w"), indent=1)
print(json.dumps(summary))
sys.exit(0 if summary["pass"] else 1)
