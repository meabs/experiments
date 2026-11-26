#!/usr/bin/env bash
cd "$(dirname "$0")/.."
for r in 1 2 3 4 5; do for c in M0 M1 G; do echo "$c $r"; done; done | xargs -P3 -L1 python3 -I scripts/trial2.py
echo finished > results/v2.status
