#!/usr/bin/env bash
# Copies a finished run into results/<name>, portable (GNU or BSD sed). Usage: export.sh <out dir> <results subfolder>
# Keeps every result.json (prompt, thinking and reply, as returned), run.log, server.txt and power.csv.
# Replaces the home folder with ~ and user paths and the host name with placeholders; fails if any is left, also inside .gz files.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$(cd "$1" && pwd)"; DST="$E/results/$2"
U="$(id -un)"; HOST="$(hostname -s)"; H="$HOME"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a "$SRC/" "$DST/"
scrub() { if sed --version >/dev/null 2>&1; then sed -i -E "$1" "$2"; else sed -i '' -E "$1" "$2"; fi; }
find "$DST" -type f \( -name '*.json' -o -name '*.txt' -o -name '*.csv' -o -name '*.log' \) -print0 |
  while IFS= read -r -d '' f; do scrub "s#$H#~#g; s#$HOST(\\.local)?#host.local#g; s#home-$U-#home-USER-#g; s#/$U([/\"])#/user\\1#g" "$f"; done
# The bare user name is not checked or replaced: it is a common first name and appears in the Wikipedia paragraphs.
if grep -rIl -e "$H" -e "/$U" -e "home-$U" -e "$HOST" "$DST"; then echo "personal path left in files above" >&2; exit 1; fi
find "$DST" -name '*.gz' -print0 | while IFS= read -r -d '' f; do
  if gzip -dc "$f" | grep -q -e "/$U" -e "home-$U" -e "$HOST"; then echo "personal path left in $f" >&2; exit 1; fi
done
du -sh "$DST"
