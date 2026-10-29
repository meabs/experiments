#!/usr/bin/env bash
# Runs the security tests for the endpoint being worked on (src/test/java/com/example/accounts/authz/), offline.
# Exit 0 only if they all pass.
set -uo pipefail
cd "$(dirname "$0")/.."
mvn -B -o -q test -Dtest='*AuthzTest' -Dsurefire.failIfNoSpecifiedTests=false > target-authz.log 2>&1
rc=$?
grep -hE "Tests run:|FAIL|expected" target-authz.log | grep -v "^\[INFO\]" | head -40
if [ $rc -eq 0 ]; then echo "verify-authz: all security tests passed"; else echo "verify-authz: FAILED (full log: target-authz.log)"; fi
rm -f target-authz.log
exit $rc
