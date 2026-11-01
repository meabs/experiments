#!/usr/bin/env bash
# Main run, ticket only (T): 7 tasks x 5 runs, shuffled, 3 at a time, then graded. The interview arms go through relay.py.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${GVP_WORK:-$HOME/code/benchmark/gvp-work}"
runs=()
for t in S1 S2 L1 L2 M1 N1 N2; do for i in 1 2 3 4 5; do runs+=("$t:main-$t-T-$i"); done; done
one() { IFS=: read -r t r <<< "$1"; [ -d "$W/$r" ] && exit 0
  python3 -I "$E/scripts/run.py" new "$r" --task "$t" --arm T >/dev/null && python3 -I "$E/scripts/run.py" auto "$r" && python3 -I "$E/scripts/run.py" grade "$r"; }
export -f one; export E W
printf '%s\n' "${runs[@]}" | shuf --random-source=<(yes) | xargs -P 2 -I{} bash -c 'one {}'
