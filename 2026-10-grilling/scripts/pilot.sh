#!/usr/bin/env bash
# Pilot for the ceiling (second pilot, after the brief check): ticket only (T) on each stage 1 task, and no docs (N)
# on each stage 2 follow-up, 2 runs each, 3 at a time, then graded.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${GRILL_WORK:-$HOME/code/benchmark/grilling-work}"
runs=()
for t in C1 C2 S1 S2 L1 L2; do for i in 1 2; do runs+=("$t:T:1:pilot-$t-T-$i"); done; done   # skipped if present
for t in S1 S2 L1 L2; do for i in 1 2; do runs+=("$t:N:2:pilot-${t}F-N-$i"); done; done
one() { IFS=: read -r t a s r <<< "$1"; [ -d "$W/$r" ] && exit 0
  python3 -I "$E/scripts/run.py" new "$r" --task "$t" --arm "$a" --stage "$s" >/dev/null && python3 -I "$E/scripts/run.py" auto "$r" && python3 -I "$E/scripts/run.py" grade "$r"; }
export -f one; export E W
printf '%s\n' "${runs[@]}" | xargs -P 3 -I{} bash -c 'one {}'
