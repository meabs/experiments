#!/usr/bin/env bash
cd "$(dirname "$0")/.."
for r in 1 2 3 4 5; do echo "M2 $r"; done | xargs -P3 -L1 python3 -I scripts/trial2.py
echo finished > results/v2b.status
