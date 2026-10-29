#!/usr/bin/env bash
# Builds the starter repository, one commit of app/, under $SEC_WORK (default ~/code/benchmark/sec-authz-work).
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${SEC_WORK:-$HOME/code/benchmark/sec-authz-work}"
R="$W/accounts-service"
rm -rf "$R"; mkdir -p "$R"
rsync -a --exclude target "$E/app/" "$R/"
git -C "$R" init -q
git -C "$R" -c user.name=trial -c user.email=trial@example.com add -A
git -C "$R" -c user.name=trial -c user.email=trial@example.com commit -q -m "accounts-service"
echo "$R $(git -C "$R" rev-parse --short HEAD)"
