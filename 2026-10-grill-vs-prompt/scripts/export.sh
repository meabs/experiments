#!/usr/bin/env bash
# Copies the runs into results/: each run's turns (developer replies and their labels, the agent's messages, Codex's
# event stream gzipped), meta.json, grade.json, audit.json and the change it made (ws.diff, against the starting commit,
# new files included). Leaves out ws/ (the checkout) and codex-home/ (the login and raw session files, which carry
# account ids). Home folder, user name and host are replaced. Fails if any personal data is left, including in .gz files.
# Usage: export.sh            (main runs and interviews -> results/main; pilots and dry runs -> results/pilot)
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${GVP_WORK:-$HOME/code/benchmark/gvp-work}"
U="$(whoami)"; HOST="$(hostname -s)"
copy() {  # <run> <dest folder>
  local r="$1" d="$2/$1"
  mkdir -p "$d"
  rsync -a --exclude 'failed-*' "$W/$r/turns" "$d/"
  for f in meta.json grade.json audit.json; do [ -f "$W/$r/$f" ] && cp "$W/$r/$f" "$d/"; done
  if [ -d "$W/$r/ws/.git" ]; then
    (cd "$W/$r/ws" && git add -A -N . 2>/dev/null; git diff --no-color HEAD -- . ':(exclude)target') > "$d/ws.diff" || true
  fi
}
rm -rf "$E/results/main" "$E/results/pilot"; mkdir -p "$E/results/main" "$E/results/pilot"
for d in "$W"/main-* "$W"/i[0-9][0-9][0-9]-*; do [ -d "$d" ] && copy "$(basename "$d")" "$E/results/main"; done
for d in "$W"/pilot-* "$W"/dry-*; do [ -d "$d" ] && copy "$(basename "$d")" "$E/results/pilot"; done
[ -f "$W/key.json" ] && cp "$W/key.json" "$E/results/main/key.json"
for f in main-scripted.log grade-interviews.log audit.log; do [ -f "$W/$f" ] && cp "$W/$f" "$E/results/main/"; done
find "$E/results/main" "$E/results/pilot" -type f \( -name '*.json' -o -name '*.log' -o -name '*.md' -o -name '*.diff' \
  -o -name '*.jsonl' -o -name '*.stderr' \) -print0 | xargs -0 perl -pi -e "s#\Q$HOME\E#~#g; s#\Q$HOST\E#host#g; s#\b\Q$U\E\b#user#g"
find "$E/results/main" "$E/results/pilot" -type f -name '*.jsonl' -exec gzip -9 {} +
PAT="$HOME|\\b$U\\b|$HOST|account_id\"|creator_user_id|auth\\.json|@hotmail|privaterelay"
if grep -rIilE "$PAT" "$E/results/main" "$E/results/pilot"; then echo "personal data left in the files above" >&2; exit 1; fi
find "$E/results/main" "$E/results/pilot" -name '*.gz' -print0 | while IFS= read -r -d '' f; do
  if gzip -dc "$f" | grep -qiE "$PAT"; then echo "personal data left in $f" >&2; exit 1; fi
done
du -sh "$E/results/main" "$E/results/pilot"
