#!/usr/bin/env bash
# Checks the hidden tests: every reference meets every requirement, and the untouched app passes no ticket.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
APP="$E/../2026-10-sec-authz/app"
R="$E/reference"
summ() { python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["task"], "ticket_pass", r["ticket_pass"], "ticket", r["ticket"], "reqs", r["reqs"], "met", r["met"], "/", r["possible"], "failed", r["failed"][:6], r.get("build_log","")[-600:])'; }
for t in ${@:-S1 S2 L1 L2 M1 N1 N2}; do
  echo "reference $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "$E/starter" "$R/base" "$R/$t" | summ
  echo "untouched app, $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "$E/starter" | summ
done
