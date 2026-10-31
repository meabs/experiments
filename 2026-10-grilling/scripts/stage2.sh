#!/usr/bin/env bash
# Stage 2: one docs run (D) per grill-with-docs run on S1, S2, L1, L2 (its GLOSSARY.md and docs/adr/, if any), and the
# same number of no-docs runs (N), 3 at a time, then graded. Needs the interview key, so it runs after every interview.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${GRILL_WORK:-$HOME/code/benchmark/grilling-work}"
runs=$(python3 -I - "$W/key.json" <<'PY'
import json, sys
k = json.load(open(sys.argv[1]))
for rid, v in sorted(k.items()):
    if v["arm"] == "GD" and v["task"] in ("S1", "S2", "L1", "L2"):
        print(f'{v["task"]}:D:s2-{v["task"]}-D-{v["rep"]}:{rid}')
        print(f'{v["task"]}:N:s2-{v["task"]}-N-{v["rep"]}:')
PY
)
one() { IFS=: read -r t a r src <<< "$1"; [ -d "$W/$r" ] && exit 0
  extra=(); [ -n "$src" ] && extra=(--docs-from "$src")
  python3 -I "$E/scripts/run.py" new "$r" --task "$t" --arm "$a" --stage 2 "${extra[@]}" >/dev/null && python3 -I "$E/scripts/run.py" auto "$r" && python3 -I "$E/scripts/run.py" grade "$r"; }
export -f one; export E W
printf '%s\n' $runs | shuf | xargs -P 3 -I{} bash -c 'one {}'
