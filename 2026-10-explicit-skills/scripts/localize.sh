#!/usr/bin/env bash
# Writes *.local.toml for each trial file, with /Users/USER replaced by this machine's home folder.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
for f in trial trial-agentsmd; do
  [ -f "$E/$f.toml" ] && sed "s#/Users/USER#$HOME#g" "$E/$f.toml" > "$E/$f.local.toml"
done
