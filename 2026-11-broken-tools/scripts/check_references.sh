#!/usr/bin/env bash
# Checks the grader: each reference is correct under every fault's files, and the untouched starter isn't.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
APP="$E/../2026-10-sec-authz/app"
R="$E/reference"
declare -A H=([C1]=C1 [C2]=C2 [L1X]=L1 [S2X]=S2)
summ() { python3 -c 'import json,sys; r=json.load(sys.stdin); print("  correct", r["correct"], "hidden", r["hidden"], "regression", r["regression"], r["failed"][:3], r.get("build_log","")[-300:])'; }
for t in ${@:-C1 C2 L1X S2X}; do
  for f in F0 SKIP EXCL BROKEN; do
    ov=("$E/starter" "$R/base" "$R/${H[$t]}"); [ -d "$E/faults/$f" ] && [ "$f" != TRANS ] && ov+=("$E/faults/$f")
    echo "reference $t under $f:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "${ov[@]}" | summ
  done
  echo "untouched starter, $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "$E/starter" | summ
done
