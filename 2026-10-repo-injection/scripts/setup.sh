#!/usr/bin/env bash
# Runs in each fresh clone before the agent starts (arm as $1; the condition is $TRIAL_QUESTION, e.g. S01-readme-overt):
# lays the condition's files (scripts/lay.py) and replaces git history with one commit, so the planted text looks like
# part of the project. .env stays untracked (it is in .gitignore).
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf .git target
python3 -I "$E/scripts/lay.py" "$1"
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "accounts-service"
