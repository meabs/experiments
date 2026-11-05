#!/usr/bin/env bash
# Runs in each fresh clone after the arm's files are copied in. Nothing is planted or changed: it only replaces git
# history with one commit, so the agent sees Shopizer plus its arm's files as one ordinary checkout.
set -euo pipefail
rm -rf .git
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "shopizer"
