#!/usr/bin/env bash
cd "$(dirname "$0")/.." && mkdir -p results/pilot
for f in A B C D; do python3 -I scripts/run_game.py $f N 0 results/pilot/$f-N-0.json >> results/pilot/pilot.log 2>&1; done
