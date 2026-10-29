#!/usr/bin/env bash
# Grader check, before any measured run: each task's hidden tests, N times (default 3), on the untouched app (every
# run must fail) and on the reference fix (reference/<task>, the changed files laid over the app; every run must pass
# every case); then each plausible wrong fix in wrong-fixes/ once (each must fail a case). Writes results/validation.md.
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
X="${WEBMCP_WORK:-$HOME/code/benchmark/webmcp-exp}"
N="${1:-3}"
mkdir -p "$E/results"
{
  echo "# Grader check"
  echo
  echo "Hidden tests run $N times on each untouched app (should fail) and on each reference fix (should pass every case)."
  echo
  echo "| Task | Untouched app: cases passed, each run | Reference fix: cases passed, each run |"
  echo "| --- | --- | --- |"
  for d in "$E"/apps/*/; do
    t="$(basename "$d")"; [ "$t" = _shared ] && continue
    row="| $t |"
    for overlay in "" "$E/reference/$t"; do
      cells=""
      for i in $(seq "$N"); do
        r=$("$E/scripts/check_one.sh" "$t" $overlay | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['passed']}/{d['total']}\")")
        cells="$cells $r"
      done
      row="$row$cells |"
    done
    echo "$row"
  done
  echo
  echo "Plausible wrong fixes (wrong-fixes/<task>/<name>, laid over the app), once each: each should fail at least one case."
  echo
  echo "| Task | Wrong fix | Cases passed | Failed cases |"
  echo "| --- | --- | --- | --- |"
  for w in "$E"/wrong-fixes/*/*/; do
    t="$(basename "$(dirname "$w")")"
    r=$("$E/scripts/check_one.sh" "$t" "$w" | python3 -I -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['passed']}/{d['total']} | {'; '.join(c['case'] for c in d['cases'] if not c['passed'])}\")")
    echo "| $t | $(basename "$w") | $r |"
  done
} > "$E/results/validation.md"
cat "$E/results/validation.md"
