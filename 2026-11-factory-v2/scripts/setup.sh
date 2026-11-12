#!/usr/bin/env bash
# Runs in each fresh clone before the agent starts (arm given as $1). Arm A (plain): nothing is added. Arm B (factory):
# the Design Factory snapshot in factory/ (AGENTS.md, CLAUDE.md, okf/, skills/, tools/) is copied in. Git history is
# then replaced with one commit, so the diff afterwards is the agent's work only.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
ARM="$1"
if [ "$ARM" = D ]; then
  cp -r "$E/factory-v2/AGENTS.md" "$E/factory-v2/CLAUDE.md" "$E/factory-v2/okf" "$E/factory-v2/skills" "$E/factory-v2/tools" .
fi
rm -rf .git
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "Brindle Bank design workspace"
