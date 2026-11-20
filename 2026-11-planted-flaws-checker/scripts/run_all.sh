#!/usr/bin/env bash
# 20 sessions, four at a time (one repetition of all four team types per group), each in its own database, merged at the end.
set -e
cd "$(dirname "$0")/.."
mkdir -p results/runs
seq 1 20 | xargs -P4 -I{} sh -c 'python3 -I scripts/room.py run --session {} --adapter real --max-messages 120 --budget-usd 1.2 --db results/runs/s{}.sqlite > results/runs/s{}.log 2>&1'
python3 -I scripts/merge.py
