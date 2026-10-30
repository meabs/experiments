#!/usr/bin/env bash
# Renders each diagram (diagrams/*.html, 1800 px wide) to PNG with headless Chrome.
# Usage: bash diagrams/render.sh [out dir]   (default: diagrams/png)
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$D/png}"
mkdir -p "$OUT"
[ -f "$D/Inter.ttf" ] || cp "$HOME/code/benchmark/fonts/Inter.ttf" "$D/Inter.ttf"   # Inter, SIL Open Font Licence; not committed
for f in "$D"/*.html; do
  n="$(basename "$f" .html)"
  h="$(grep -o 'height="[0-9]*"' "$f" | head -1 | tr -dc 0-9)"
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=1800,"$h" --screenshot="$OUT/$n.png" "file://$f" >/dev/null 2>&1
  echo "$OUT/$n.png"
done
