#!/usr/bin/env bash
# Runs in each fresh clone after the arm overlay: applies the task's plant (if it has one), then replaces git history
# with one commit so the agent cannot find the plant (or the overlay) by diffing.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
P="$E/tasks/${TRIAL_QUESTION:-none}/plant.patch"
if [ -f "$P" ]; then git apply "$P"; fi
rm -rf .git
git init -q
git -c user.name=trial -c user.email=trial@example.com add -A
git -c user.name=trial -c user.email=trial@example.com commit -q -m "shopizer"
