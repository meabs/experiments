#!/usr/bin/env bash
# Main run: reps 1-3, interleaved by rep, fixture, arm. Resumable: finished games are skipped. STOP file ends it.
cd "$(dirname "$0")/.." && mkdir -p results/main-huihui
for rep in 1 2 3; do for f in A B C D; do for a in F S M N; do
  [ -f results/main-huihui/STOP ] && exit 0
  o=results/main-huihui/$f-$a-$rep.json; [ -f "$o" ] && continue
  python3 -I scripts/run_game.py $f $a $rep "$o.tmp" --model huihui_ai/Qwen3.8-abliterated:latest >> results/main-huihui/main.log 2>&1 && mv "$o.tmp" "$o"
done; done; done
