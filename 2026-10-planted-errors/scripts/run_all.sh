#!/usr/bin/env bash
# Runs every item (README, "Procedure") with APU power logged, and records the server and model actually used.
# Usage: run_all.sh <out dir>
set -uo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"; OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
{ curl -s localhost:11434/api/version; echo; curl -s localhost:11434/api/tags; echo;
  curl -s localhost:11434/api/show -d '{"model":"qwen3.8:27b"}' | python3 -I -c "import json,sys;d=json.load(sys.stdin);print(json.dumps({k:d.get(k) for k in ('details','parameters','model_info')})[:4000])"
  systemctl show ollama -p Environment; } > "$OUT/server.txt" 2>&1
bash ~/code/benchmark/local-setup/powerlog.sh "$OUT/power.csv" & PW=$!
python3 -I "$E/scripts/run.py" "$OUT/items" "$E/items/items.json" > "$OUT/run.log" 2>&1
kill "$PW"
echo "done: $(ls "$OUT/items" | wc -l) items"
