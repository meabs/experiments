#!/usr/bin/env bash
# Writes trial.local.toml and gate.local.toml with /Users/USER replaced by this machine's home folder.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
for f in trial calibration; do sed "s#/Users/USER#$HOME#g" "$E/$f.toml" > "$E/$f.local.toml"; done
