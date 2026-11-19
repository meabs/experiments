#!/usr/bin/env bash
# Five sessions in order (notes carry over). Needs OPENROUTER_API_KEY (any placeholder if the proxy injects the key).
set -e
cd "$(dirname "$0")/.."
for n in 1 2 3 4 5; do
  python3 -I scripts/room.py run --session $n --adapter real --max-messages 120 --budget-usd 2 --db results/events.sqlite
done
