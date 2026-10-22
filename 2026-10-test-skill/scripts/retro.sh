#!/usr/bin/env bash
# Rebuilds an earlier run's final state from its saved diff and runs the relevance check on it.
# Usage: retro.sh <saved run dir> <shopizer source repo> <out dir>
# The clone is rebuilt as the rig did: shopizer at 6a4a0a6, the task's plant, one commit; then the agent's diff on top.
# Arm overlays are left out: they hold only AGENTS.md and skills, which no test reads.
set -euo pipefail
RUN="$1"; SRC="$2"; OUT="$3"
E="$(cd "$(dirname "$0")/.." && pwd)"
T=$(echo "$RUN" | awk -F/ '{print $(NF-3)}')
mkdir -p "$OUT"
W="$(mktemp -d "${TMPDIR:-/tmp}/retro.XXXXXX")"
git -C "$SRC" archive 6a4a0a6 | tar -x -C "$W"
cd "$W"
[ -f "$E/tasks/$T/plant.patch" ] && git apply "$E/tasks/$T/plant.patch"
git init -q && git -c user.name=t -c user.email=t@e add -A && git -c user.name=t -c user.email=t@e commit -qm shopizer
git apply --whitespace=nowarn "$RUN/agent.diff"
bash "$E/scripts/relevance.sh" "$OUT/relevance.json" "$OUT"
cd / && rm -rf "$W"
