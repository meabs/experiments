#!/usr/bin/env bash
# Runs both answer models over every question (README, "Procedure"), 27B then 8B, with APU power logged, and records
# the server and models actually used. Usage: run_all.sh <out dir>
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
{ curl -s localhost:11434/api/version; echo; curl -s localhost:11434/api/tags; echo
  for m in qwen3.8:27b qwen3:8b bge-m3; do curl -s localhost:11434/api/show -d "{\"model\":\"$m\"}" | python3 -I -c "import json,sys;d=json.load(sys.stdin);print('$m', json.dumps({k:d.get(k) for k in ('details','parameters')}))"; done
  systemctl show ollama -p Environment; } > "$OUT/server.txt" 2>&1
bash ~/code/benchmark/local-setup/powerlog.sh "$OUT/power.csv" & PW=$!
for m in qwen3.8:27b qwen3:8b; do python3 -I "$E/scripts/run.py" "$OUT" "$m" "$E/items/items.json" "$E/items/retrieved.json"; done > "$OUT/run.log" 2>&1
kill "$PW"
echo "done: $(find "$OUT" -name result.json | wc -l) answers"
