#!/usr/bin/env bash
# Checks the grader and the gates: each reference is correct under every condition; the untouched starter isn't; arm M's
# gate passes on each reference under F0 and fails under EXCL, EXCL1 and STALE; arm C's gate passes under all three.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
APP="$E/../2026-10-sec-authz/app"
R="$E/reference"
declare -A H=([C1]=C1 [C2]=C2 [L1X]=L1 [S2X]=S2)
summ() { python3 -c 'import json,sys; r=json.load(sys.stdin); print("  correct", r["correct"], "hidden", r["hidden"], "regression", r["regression"], r["failed"][:3], r.get("build_log","")[-300:])'; }
gate() {  # gate <arm> <task> <condition>
  local tmp; tmp=$(mktemp -d)
  cp -r "$APP" "$tmp/ws"; rm -rf "$tmp/ws/target"
  for o in "$E/starter" "$R/base" "$R/${H[$2]}" "$E/arms/$1"; do cp -r "$o/." "$tmp/ws/"; done
  [ "$3" != F0 ] && cp -r "$E/faults/$3/." "$tmp/ws/"
  (cd "$tmp/ws" && bash scripts/verify.sh | grep -E "^(TESTS RUN|EXPECTED|MISSING|verify:)" | tr '\n' ' '; echo " exit ${PIPESTATUS[0]}")
  rm -rf "$tmp"
}
for t in ${@:-C1 C2 L1X S2X}; do
  for f in F0 EXCL EXCL1; do
    ov=("$E/starter" "$R/base" "$R/${H[$t]}"); [ "$f" != F0 ] && ov+=("$E/faults/$f")
    echo "reference $t under $f:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "${ov[@]}" | summ
    echo "  gate C: $(gate C "$t" "$f")"
    echo "  gate M: $(gate M "$t" "$f")"
  done
  echo "  gate M under STALE: $(gate M "$t" STALE)"
  echo "untouched starter, $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "$E/starter" | summ
done
