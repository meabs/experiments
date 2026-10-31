#!/usr/bin/env bash
# Checks the hidden tests: every reference meets every requirement, and the untouched app passes no ticket.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
APP="$E/../2026-10-sec-authz/app"
R="$E/reference"
summ() { python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["task"], "ticket_pass", r["ticket_pass"], "ticket", r["ticket"], "reqs", r["reqs"], "met", r["met"], "/", r["possible"], "failed", r["failed"][:6], r.get("build_log","")[-600:])'; }
for t in ${@:-C1 C2 S1 S2 L1 L2 S1F S2F L1F L2F}; do
  ST="$E/starter"
  case $t in *F) ov="$ST $R/base $R/${t%F} $R/$t";; *) ov="$ST $R/base $R/$t";; esac
  echo "reference $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay $ov | summ
  case $t in *F) echo "stage-1 reference only, $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "$ST" "$R/base" "$R/${t%F}" | summ;;
             *) echo "untouched app, $t:"; python3 -I "$E/scripts/grade.py" "$t" "$APP" --overlay "$ST" | summ;; esac
done
