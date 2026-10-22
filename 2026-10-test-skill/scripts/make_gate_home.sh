#!/usr/bin/env bash
# Builds the clean home for arm F (gate): the same as home-clean (login, git identity, Maven repository link, no skills,
# no memories), plus a Stop hook that runs gate.sh. The gate scripts are copied into the home, because the rig hides the
# experiments folder from the agent and its hooks.
# Usage: make_gate_home.sh <work dir, e.g. ~/code/benchmark/skills-impact-work>
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="$1"; SRC="$W/home-clean"; H="$W/home-gate"
rm -rf "$H"; mkdir -p "$H/.codex/gate" "$H/.codex/skills"
cp "$SRC/.gitconfig" "$H/.gitconfig"
ln -s "$(readlink "$SRC/.m2")" "$H/.m2"
cp "$SRC/.codex/auth.json" "$H/.codex/auth.json"
: > "$H/.codex/config.toml"
cp "$E/scripts/gate.sh" "$E/scripts/relevance.sh" "$E/scripts/relevance.py" "$H/.codex/gate/"
chmod +x "$H/.codex/gate/"*.sh
cat > "$H/.codex/hooks.json" <<EOF
{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "$H/.codex/gate/gate.sh", "timeout": 900}]}]}}
EOF
echo "gate home at $H"
