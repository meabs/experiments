#!/usr/bin/env bash
# Usage: run_batch.sh <jobs file: "ARM SCEN REP" per line> <out dir> [parallel]   (finished trajectories are skipped)
J="$1"; O="$(mkdir -p "$2" && cd "$2" && pwd)"; P="${3:-3}"; H="$(cd "$(dirname "$0")" && pwd)"
while read -r arm scen rep; do
  [ -f "$O/runs/$scen/$arm/$rep/result.json" ] || echo "$arm $scen $rep"
done < "$J" | xargs -P"$P" -L1 bash -c 'python3 -I '"$H"'/run_traj.py "$0" "$1" "$2" '"$O"' >> '"$O"'/batch.log 2>&1'
