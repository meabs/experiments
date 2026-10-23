#!/usr/bin/env bash
# Copies one driver run (egm_drive.sh) into results/<run>: the turns, the messages sent, the Codex sessions, the approved
# design and EGM's review reports, the grade, the session audit, and (if given) a log of the Claude approver's messages,
# tool calls and replies, and its audit. Home folder and user name replaced, large files gzipped, then checked for personal paths.
# Usage: export_run.sh <run> [approver transcript .jsonl]
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${EGM_WORK:-$HOME/code/benchmark/skills-impact-work}"
R="$W/egm-runs/$1"; D="$E/results/$1"
U="$(whoami)"; HOST="$(hostname -s)"
rm -rf "$D"; mkdir -p "$D/turns" "$D/sessions" "$D/grade" "$D/design"
cp "$R"/turns/* "$D/turns/"; cp "$R/isolate.sb" "$R/task" "$D/"
[ -d "$R/msgs" ] && cp -R "$R/msgs" "$D/msgs"
cp "$R/approved_design.md" "$D/design/"
for f in "$R"/repo/*_report.md; do [ -e "$f" ] && cp "$f" "$D/design/"; done
find "$R/home/.codex/sessions" -name '*.jsonl' -exec cp {} "$D/sessions/" \;
rsync -a "$R/grade/runs/$(cat "$R/task")/egm/codex/1/" "$D/grade/"
python3 -I "$E/scripts/audit_sessions.py" "$D/sessions" > "$D/audit.md"
if [ -n "${2:-}" ]; then
  python3 -I "$E/scripts/approver_log.py" "$2" > "$D/approver-log.md"   # never the raw transcript: it holds account details
  python3 -I "$E/scripts/audit_approver.py" "$2" "$R/repo" > "$D/approver-audit.md"
fi
find "$D" -type f \( -name '*.json' -o -name '*.jsonl' -o -name '*.log' -o -name '*.out' -o -name '*.err' -o -name '*.diff' \
  -o -name '*.md' -o -name '*.sb' -o -name '*.numstat' -o -name '*.args' \) \
  -exec sed -i '' -E "s#$HOME#~#g; s#$HOST(\\.local)?#host.local#g; s#Users-$U-#Users-USER-#g; s#$U#user#g" {} +
find "$D" -type f \( -name '*.jsonl' -o -name '*-mvn.log' -o -name 'relevance-*.log' \) -exec gzip -9 {} +
if grep -rIil "$HOME\|$U" "$D"; then echo "personal path left in files above" >&2; exit 1; fi
for f in $(find "$D" -name '*.gz'); do gzip -dc "$f" | grep -qi "$U" && { echo "personal path left in $f" >&2; exit 1; }; done
du -sh "$D"
