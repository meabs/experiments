#!/usr/bin/env bash
# Runs in each fresh clone before the agent starts (arm given as $1: A, B or C): lays the arm's files over the
# repository (AGENTS.md; for B the okf/ bundle) and replaces git history with one commit, so every arm starts from a
# single commit and the diff afterwards is the agent's work only.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
ARM="$1"
cp -r "$E/arms/$ARM/." .
rm -rf .git target
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "accounts-service"
