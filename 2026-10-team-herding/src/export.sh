#!/usr/bin/env bash
# Exports one run's calls.jsonl for publishing: personal paths replaced, gzipped, and checked. The agent homes (which
# hold the login) and the work folders are not exported. Portable (no BSD sed -i '').
# Usage: bash src/export.sh <out dir> <results subfolder name>
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$1"; DEST="$E/results/$2"; mkdir -p "$DEST"
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
sed -e "s#$OUT#<out>#g" -e "s#$U#~#g" "$OUT/calls.jsonl" | gzip -9n > "$DEST/calls.jsonl.gz"
sed -e "s#$OUT#<out>#g" -e "s#$U#~#g" "$OUT/environment.json" > "$DEST/environment.json"
if zcat "$DEST/calls.jsonl.gz" | cat - "$DEST/environment.json" | grep -q -e "$U" -e "$(id -un)@" ; then
  echo "personal path left in $DEST" >&2; exit 1
fi
echo "exported $(zcat "$DEST/calls.jsonl.gz" | wc -l) calls to $DEST"
