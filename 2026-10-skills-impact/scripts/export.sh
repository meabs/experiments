#!/usr/bin/env bash
# Copies a finished stage into results/, with the home folder replaced by ~ and large logs gzipped.
# Usage: export.sh <stage dir> <results subfolder>. Skips work/ (the clones) and the sandbox profiles.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$1"; DST="$E/results/$2"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a --exclude work --exclude isolate.sb --exclude '*.orig' "$SRC/" "$DST/"
find "$DST" -type f \( -name '*.json' -o -name '*.log' -o -name '*.out' -o -name '*.err' -o -name '*.diff' -o -name '*.md' \) \
  -exec sed -i '' "s#$HOME#~#g" {} +
find "$DST" -type f \( -name raw.out -o -name '*-mvn.log' \) -exec gzip -9 {} +
if grep -rIl "$HOME" "$DST"; then echo "home path left in files above" >&2; exit 1; fi
du -sh "$DST"
