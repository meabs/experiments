#!/usr/bin/env bash
# Runs in each fresh copy of a task app before the agent starts (arm given as $1: plain, tool or tool-recipes):
# lays the arm's files over the app, gives this run its own port (so parallel runs don't collide), links the arm's
# Python environment as .venv, and replaces git history with one commit.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
X="${WEBMCP_WORK:-$HOME/code/benchmark/webmcp-exp}"
ARM="$1"
cp -r "$E/arms/$ARM/." .
PORT=$(( 20000 + $(printf '%s' "$TRIAL_ID" | cksum | cut -d' ' -f1) % 20000 ))
grep -rl '{{PORT}}' . --exclude-dir=.git | xargs -r sed -i "s/{{PORT}}/$PORT/g"
if [ "$ARM" = plain ]; then ln -s "$X/env-plain" .venv; else ln -s "$X/env-tool" .venv; fi
printf '.venv\n.webmcp/runs/\n' > .git-info-exclude
rm -rf .git
git init -q
mv .git-info-exclude .git/info/exclude
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "page"
