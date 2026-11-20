#!/usr/bin/env bash
# Four sessions, interleaved: 1 BELBIN, 2 CONTROL, 3 BELBIN (roles reversed across letters), 4 CONTROL.
set -e
cd "$(dirname "$0")/.."
for n in 1 2 3 4; do
  python3 -I scripts/room.py run --session $n --adapter real --max-messages 150 --budget-usd 2 --db results/events.sqlite
done
