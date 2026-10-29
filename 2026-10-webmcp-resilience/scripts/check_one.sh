#!/usr/bin/env bash
# Runs one task's hidden tests on the untouched app, or with an overlay of changed files (a reference fix or a trial
# fix) laid over a copy of it. Usage: check_one.sh <task> [overlay-dir]. Prints the JSON summary.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
X="${WEBMCP_WORK:-$HOME/code/benchmark/webmcp-exp}"
T="$(mktemp -d)"
cp -r "$E/apps/$1/." "$T/"
[ -n "${2:-}" ] && cp -r "$2/." "$T/"
(cd "$E/hidden" && "$X/env-plain/bin/python" "${1//-/_}.py" "$T" 2>/dev/null)
rc=$?
rm -rf "$T"
exit $rc
