#!/bin/bash
# Main run stage 1: seeds 1-4 (SEEDS="5 6" to extend), arms interleaved, resumable. Start only when no other model run is using the GPU.
cd "$(dirname "$0")/.." || exit 1
PY=/home/garry/code/benchmark/trials/pha-venv/.venv/bin/python
mkdir -p results/main
for seed in ${SEEDS:-1 2 3 4}; do for arm in A B C D; do
  [ -f results/main/$arm-s$seed/result.json ] && continue
  $PY -I scripts/kf.py --arm $arm --seed $seed --out "$PWD/results/main" >> results/main.log 2>&1
done; done
