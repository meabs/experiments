#!/usr/bin/env bash
# Copies one trial's results into results/<name>, with the home folder replaced by ~, the user name and host replaced,
# and large logs gzipped. Leaves out work/ (the clones) and agent-homes/ (each run's Codex home: the login and the raw
# session files, which carry account ids). The rig's event stream (raw.out) and each run's sessions.json audit are kept.
# Fails if a personal path, user name, host name or account id is left, including inside .gz files. GNU and BSD safe.
# Usage: export.sh <trial out dir> <results subfolder>
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$1"; DST="$E/results/$2"
U="$(whoami)"; HOST="$(hostname -s)"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a --exclude work --exclude agent-homes --exclude '*.orig' "$SRC/" "$DST/"
find "$DST" -type f \( -name '*.json' -o -name '*.log' -o -name '*.out' -o -name '*.err' -o -name '*.diff' -o -name '*.txt' \
  -o -name '*.numstat' -o -name '*.md' \) -print0 |
  xargs -0 perl -pi -e "s#\Q$HOME\E#~#g; s#\Q$HOST\E#host#g; s#\b\Q$U\E\b#user#g"
find "$DST" -type f \( -name raw.out -o -name raw.err \) -exec gzip -9 {} +
PAT="$HOME|\\b$U\\b|$HOST|account_id\"|creator_user_id|auth\\.json|@hotmail|privaterelay"
if grep -rIilE "$PAT" "$DST"; then echo "personal data left in the files above" >&2; exit 1; fi
find "$DST" -name '*.gz' -print0 | while IFS= read -r -d '' f; do
  if gzip -dc "$f" | grep -qiE "$PAT"; then echo "personal data left in $f" >&2; exit 1; fi
done
du -sh "$DST"
