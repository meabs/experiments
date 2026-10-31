#!/usr/bin/env bash
# Main run, scripted arms: ticket only (T) and grilling with "yes" to everything (GY), 3 runs per task, 3 at a time,
# in a shuffled order, then graded. The interview arms (Q, G, GD) go through relay.py.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${GRILL_WORK:-$HOME/code/benchmark/grilling-work}"
runs=()
for t in C1 C2 S1 S2 L1 L2; do for a in T GY; do for i in 1 2 3; do runs+=("$t:$a:main-$t-$a-$i"); done; done; done
one() { IFS=: read -r t a r <<< "$1"; [ -d "$W/$r" ] && exit 0
  python3 -I "$E/scripts/run.py" new "$r" --task "$t" --arm "$a" >/dev/null && python3 -I "$E/scripts/run.py" auto "$r" && python3 -I "$E/scripts/run.py" grade "$r"; }
export -f one; export E W
printf '%s\n' "${runs[@]}" | shuf | xargs -P 3 -I{} bash -c 'one {}'
