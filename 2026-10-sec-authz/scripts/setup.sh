#!/usr/bin/env bash
# Runs in each fresh clone before the agent starts (arm given as $1: A, B, C or D; the task is $TRIAL_QUESTION):
# lays the arm's files over the repository (AGENTS.md; for B and D the skill; for C and D the gate script), adds the
# task's public security tests for C and D, and replaces git history with one commit.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
ARM="$1"
cp -r "$E/arms/$ARM/." .
if [ "$ARM" = C ] || [ "$ARM" = D ]; then
  mkdir -p src/test/java/com/example/accounts/authz
  cp "$E/gate/${TRIAL_QUESTION}AuthzTest.java" src/test/java/com/example/accounts/authz/
fi
rm -rf .git target
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "accounts-service"
