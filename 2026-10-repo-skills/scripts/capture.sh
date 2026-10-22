#!/usr/bin/env bash
# Verify step of the generation run (generate/generate.toml): saves the agent's whole diff, and copies AGENTS.md and
# .agents/ (the only files the brief allows) to <out>/runs/.../generated/. Exit 0 if AGENTS.md and at least one skill exist.
set -uo pipefail
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R/generated"
git add -A -N . 2>/dev/null
git diff --stat -- . ':(exclude)**/target/**' > "$R/agent.diffstat"
git diff -- . ':(exclude)**/target/**' > "$R/agent.diff"
[ -f AGENTS.md ] && cp AGENTS.md "$R/generated/"
[ -d .agents ] && cp -R .agents "$R/generated/"
[ -f AGENTS.md ] && ls .agents/skills/*/SKILL.md >/dev/null 2>&1
