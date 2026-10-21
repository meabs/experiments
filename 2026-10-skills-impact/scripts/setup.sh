#!/usr/bin/env bash
# Runs in each fresh clone after the arm overlay: plants the BUG task, then replaces git history with one commit
# so the agent cannot find the plant (or the overlay) by diffing.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
if [ "${TRIAL_QUESTION:-}" = "BUG" ]; then git apply "$E/tasks/BUG/plant.patch"; fi
rm -rf .git
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "shopizer"
