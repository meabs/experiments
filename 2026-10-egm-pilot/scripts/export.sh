#!/usr/bin/env bash
# Copies a finished stage into results/, with the home folder replaced by ~ and large logs gzipped.
# Usage: export.sh <stage dir> <results subfolder>. Skips work/ (the clones) and the sandbox profiles.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$1"; DST="$E/results/$2"
U="$(whoami)"; HOST="$(hostname -s)"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a --exclude work --exclude isolate.sb --exclude '*.orig' "$SRC/" "$DST/"
find "$DST" -type f \( -name '*.json' -o -name '*.log' -o -name '*.out' -o -name '*.err' -o -name '*.diff' -o -name '*.md' \) \
  -exec sed -i '' -E "s#$HOME#~#g; s#$HOST(\\.local)?#host.local#g; s#Users-$U-#Users-USER-#g; s#$U#user#g" {} +
find "$DST" -type f \( -name raw.out -o -name '*-mvn.log' -o -name 'relevance-*.log' \) -exec gzip -9 {} +
if grep -rIil "$HOME\|$U" "$DST"; then echo "personal path left in files above" >&2; exit 1; fi
for f in $(find "$DST" -name '*.gz'); do gzip -dc "$f" | grep -qi "$U" && { echo "personal path left in $f" >&2; exit 1; }; done
du -sh "$DST"
