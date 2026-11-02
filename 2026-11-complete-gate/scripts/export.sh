#!/usr/bin/env bash
# Copies a batch's runs into results/<batch>/ for publication: meta, event stream (gzipped), final message, diff,
# grade, facts, judge labels and the key. Never the Codex home (it holds the login). Fails if any personal path is
# left, including inside the .gz files.
# Usage: scripts/export.sh pilot|main
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
B="$1"; SRC="${BRK_WORK:-$HOME/code/benchmark/brk-work}/$B"; OUT="$E/results/$B"
rm -rf "$OUT"; mkdir -p "$OUT"
cp "$SRC/key.json" "$OUT/"
for d in "$SRC"/[pm][0-9][0-9][0-9]; do
  r="$(basename "$d")"; mkdir -p "$OUT/$r"
  for f in meta.json final.md ws.diff grade.json facts.json judge.json; do [ -f "$d/$f" ] && cp "$d/$f" "$OUT/$r/"; done
  gzip -c "$d/events.jsonl" > "$OUT/$r/events.jsonl.gz"
done
# anonymise the home directory and user name everywhere, then check
U="$(id -un)"; H="$HOME"
python3 - "$OUT" "$H" "$U" <<'PY'
import gzip, os, sys
out, home, user = sys.argv[1:]
for root, _, files in os.walk(out):
    for f in files:
        p = os.path.join(root, f)
        op = gzip.open if f.endswith(".gz") else open
        with op(p, "rt") as fh:
            s = fh.read()
        t = s.replace(home, "~").replace(f"/{user}/", "/USER/").replace(user, "USER")
        if t != s:
            with op(p, "wt") as fh:
                fh.write(t)
PY
if grep -rIl -e "$H" -e "$U" "$OUT" >/dev/null || zgrep -l -e "$H" -e "$U" "$OUT"/*/events.jsonl.gz >/dev/null 2>&1; then
  echo "personal data left in $OUT" >&2; exit 1
fi
echo "exported $(ls -d "$OUT"/[pm][0-9][0-9][0-9] | wc -l) runs to $OUT"
