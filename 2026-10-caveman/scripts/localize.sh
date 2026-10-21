#!/usr/bin/env bash
# Writes <name>.local.toml for each trial file, with /Users/USER replaced by this machine's home folder.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
for f in "$E"/trial-codex.toml "$E"/trial-cursor.toml "$E"/gate.toml; do sed "s#/Users/USER#$HOME#g" "$f" > "${f%.toml}.local.toml"; done
