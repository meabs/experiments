#!/bin/bash
# Pilot: arms A and B, seed 1. PILOT-ONLY.
cd "$(dirname "$0")/.." || exit 1
PY=/home/garry/code/benchmark/trials/pha-venv/.venv/bin/python
mkdir -p results/pilot
for arm in A B; do $PY -I scripts/kf.py --arm $arm --seed 1 --out "$PWD/results/pilot" >> results/pilot.log 2>&1; done
