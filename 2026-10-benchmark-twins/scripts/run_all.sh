#!/usr/bin/env bash
# Runs both models (README, "Procedure"): local and hosted at the same time, GSM8K then HumanEval each, with APU power
# logged during the local run. Usage: run_all.sh <out dir>
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
bash ~/code/benchmark/local-setup/powerlog.sh "$OUT/power.csv" & PW=$!
( for f in gsm8k-twins humaneval-twins-sample; do python3 -I "$E/scripts/run.py" "$OUT" hosted "$E/items/$f.json"; done ) > "$OUT/hosted.log" 2>&1 &
HO=$!
for f in gsm8k-twins humaneval-twins-sample; do python3 -I "$E/scripts/run.py" "$OUT" local "$E/items/$f.json"; done > "$OUT/local.log" 2>&1
kill "$PW"; wait "$HO"
echo "done: $(grep -c . "$OUT/local.log") local lines, $(grep -c . "$OUT/hosted.log") hosted lines"
