#!/usr/bin/env bash
# After the agent finishes (outside the sandbox): keeps the agent's work for grading. Copies every file the agent
# added or changed (except the factory's own folders) to the run folder under artefacts/, and lists them.
# Exit 0 if prototype/index.html exists. Screenshots, accessibility checks and judging run later (scripts/shoot.py).
set -uo pipefail
R="$TRIAL_OUT/runs/$TRIAL_QUESTION/$TRIAL_ARM/$TRIAL_AGENT/$TRIAL_REP"
mkdir -p "$R/artefacts"
git add -A -N . 2>/dev/null
git diff --stat -- okf skills tools AGENTS.md CLAUDE.md > "$R/factory-edits.txt" 2>/dev/null
git status --porcelain | awk '{print $2}' | grep -v -E '^(okf|skills|tools)/' > "$R/changed.txt"
git diff --numstat > "$R/agent.numstat"
while read -r f; do
  [ -e "$f" ] && mkdir -p "$R/artefacts/$(dirname "$f")" && cp -r "$f" "$R/artefacts/$f"
done < "$R/changed.txt"
find "$R/artefacts" -type f | sed "s#^$R/artefacts/##" | sort > "$R/files.txt"
echo "files $(wc -l < "$R/files.txt")"
if [ -s prototype/index.html ]; then echo ok; exit 0; fi
echo "no prototype/index.html"; exit 1
