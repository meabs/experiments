#!/usr/bin/env bash
# Stop hook for arm E (evidence-led). Codex runs it when the agent tries to finish, with a JSON event on stdin.
# It builds the agent's clone and runs the whole test suite offline (never the hidden tests, which are not there), then
# reads the surefire reports. It blocks the finish once if the build failed, any test failed or errored, or fewer tests
# ran than the existing suite runs on the original code (EXPECTED_RUN, counted once before any run). On the second stop
# (stop_hook_active true) it checks again and records the result, but always lets the agent finish. If the check itself
# can't run, the agent is never blocked.
# Each check is saved in the clone's .git folder (gate-<n>.json, gate-<n>.diff, gate-<n>-mvn.log); verify.sh copies them.
set -uo pipefail
EXPECTED_RUN=40
IN="$(cat)"
CWD="$(printf '%s' "$IN" | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["cwd"])' 2>/dev/null)"
ACTIVE="$(printf '%s' "$IN" | python3 -I -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())' 2>/dev/null)"
cd "$CWD" 2>/dev/null || { echo '{}'; exit 0; }
G="$(git rev-parse --absolute-git-dir 2>/dev/null)" || { echo '{}'; exit 0; }
n=$(ls "$G"/gate-*.json 2>/dev/null | wc -l | tr -d ' '); n=$((n + 1))
start=$(date +%s)
git add -A -N . 2>/dev/null
git diff -- . ':(exclude)*.dat' ':(exclude)**/target/**' > "$G/gate-$n.diff" 2>/dev/null
mvn -o -B -Dmaven.test.failure.ignore=true clean test > "$G/gate-$n-mvn.log" 2>&1
rc=$?
python3 -I - "$G/gate-$n.json" "$ACTIVE" "$start" "$rc" "$EXPECTED_RUN" "$G/gate-$n-mvn.log" <<'PY'
import glob, json, sys, time
import xml.etree.ElementTree as ET
p, active, start, rc, expected, log = sys.argv[1], sys.argv[2] == "true", int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
run = failed = errors = skipped = 0
failing = []
for f in glob.glob("**/target/surefire-reports/TEST-*.xml", recursive=True):
    try:
        s = ET.parse(f).getroot()
    except ET.ParseError:
        continue
    run += int(s.get("tests", 0)); failed += int(s.get("failures", 0)); errors += int(s.get("errors", 0))
    skipped += int(s.get("skipped", 0))
    for tc in s.iter("testcase"):
        if tc.find("failure") is not None or tc.find("error") is not None:
            failing.append(f'{s.get("name", "?").split(".")[-1]}.{tc.get("name")}')
executed = run - skipped
built = rc == 0
problems = []
if not built:
    tail = [l for l in open(log, errors="replace").read().splitlines() if l.startswith("[ERROR]")][:8]
    problems.append("the build failed (mvn exited " + str(rc) + "). First errors:\n" + "\n".join(tail))
if failed or errors:
    problems.append(f"{failed} tests failed and {errors} errored: " + ", ".join(failing[:10]))
if built and executed < expected:
    problems.append(f"only {executed} tests ran (not skipped); the existing suite runs {expected}, so some tests did not run")
v = {"n_run": run, "failed": failed, "errors": errors, "skipped": skipped, "executed": executed, "mvn_exit": rc,
     "expected_executed": expected, "failing": failing, "gate_seconds": int(time.time()) - start,
     "stop_hook_active": active}
msg = None
if problems and not active:
    msg = ("Before you finish, I built the project and ran the whole test suite with `mvn -o clean test`: "
           f"tests run {run}, failed {failed}, errors {errors}, skipped {skipped}. Problems:\n- " + "\n- ".join(problems) +
           "\nFix these (without disabling, deleting or weakening any test), then build and run the tests again.")
v["blocked"] = msg is not None
v["message"] = msg
json.dump(v, open(p, "w"), indent=1)
print(json.dumps({"decision": "block", "reason": msg}) if msg else "{}")
PY
