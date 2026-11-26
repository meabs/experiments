#!/usr/bin/env bash
# write phase (10 runs), then read phase (20 runs), three at a time, interleaved.
cd "$(dirname "$0")/.."
for r in 1 2 3 4 5; do for c in M G; do echo "write $c $r"; done; done | xargs -P3 -L1 python3 -I scripts/trial.py
for r in 1 2 3 4 5; do for c in M G; do for m in P K; do echo "read $c $r $m"; done; done; done | xargs -P3 -L1 python3 -I scripts/trial.py
echo finished > results/run_all.status
