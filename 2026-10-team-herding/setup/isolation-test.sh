#!/usr/bin/env bash
# Checks what an agent can see inside setup/codex-bwrap.sh: the ground truth and this folder must be invisible, the work
# folder visible. Usage: bash setup/isolation-test.sh
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"; mkdir -p "$T/work"; echo hi > "$T/work/ALERT.md"
probe() { (cd "$T/work" && AGENT_HOME="$T/home" CODEX_BIN=/bin/bash bash "$E/setup/codex-bwrap.sh" -c "$1"); }
fail=0
for p in "$E/../2026-10-evidence-manipulation/scenarios/ground_truth.json" "$E/cases.json" "$E/src/analyse.py"; do
  if probe "test -e '$p'"; then echo "VISIBLE (bad): $p"; fail=1; else echo "invisible: $p"; fi
done
probe "test -r ALERT.md" && echo "work folder readable" || { echo "work folder NOT readable"; fail=1; }
probe "ls /home" | sed 's/^/home contains: /'
rm -rf "$T"; exit $fail
