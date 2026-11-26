#!/usr/bin/env bash
# Waits until the Codex login is refreshed (auth.json newer than the marker), proves it with one real call, then runs the main
# batch (up to three passes; finished trajectories are skipped, auth-failed ones are redone).
H="$HOME/code/experiments/2026-11-release-transition"; M="$H/results/.login-marker"
until [ "$HOME/.codex/auth.json" -nt "$M" ]; do sleep 60; done
sleep 5
S="$(mktemp -d)"; mkdir -p "$S/w"; cd "$S/w" && git init -q .
TRIAL_OUT="$S" TRIAL_ID=s CODEX_PROFILE=hosted timeout 150 "$HOME/code/benchmark/local-setup/codex-bwrap.sh" exec -s danger-full-access --skip-git-repo-check --json --model gpt-5.6-luna "Reply: pong" > "$S.out" 2>&1
rm -rf "$S"
if ! grep -q '"text":"pong"' "$S.out"; then echo "login smoke failed" > "$H/results/wait_and_run.status"; rm -f "$S.out"; exit 1; fi
rm -f "$S.out"
cd "$H"
for pass in 1 2 3; do
  bash scripts/run_batch.sh results/main-jobs.txt results/main 3
  [ "$(ls results/main/runs/*/*/*/result.json 2>/dev/null | wc -l)" -ge 90 ] && break
done
echo "finished $(ls results/main/runs/*/*/*/result.json 2>/dev/null | wc -l)/90" > results/wait_and_run.status
