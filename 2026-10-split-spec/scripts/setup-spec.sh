#!/usr/bin/env bash
# Follow-up arm team-spec: the usual setup, then the task's prompt copied into the clone as TASK.md and folded into the
# single commit, so every agent can read the task word for word and TASK.md never shows in the agent's diff.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
bash "$E/scripts/setup.sh"
cp "$E/tasks/$TRIAL_QUESTION/prompt.md" TASK.md
git -c user.name=trial -c user.email=trial@example.com add TASK.md
git -c user.name=trial -c user.email=trial@example.com commit -q --amend -m "shopizer"
