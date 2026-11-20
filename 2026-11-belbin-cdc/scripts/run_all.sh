#!/usr/bin/env bash
# Four sessions, interleaved: 1 BASE, 2 FORCEFUL, 3 BASE (roles reversed across letters), 4 FORCEFUL.
set -e
cd "$(dirname "$0")/.."
for n in 1 2 3 4; do
  python3 -I scripts/room.py run --session $n --adapter real --max-messages 150 --budget-usd 2 --db results/events.sqlite
done
