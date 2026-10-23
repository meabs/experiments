#!/usr/bin/env bash
# Builds the clean home for the EGM arm: the same as home-clean (login, git identity, Maven repository link, no skills,
# no memories), plus the EGM plugin from google/elephant-goldfish-model, pinned to one commit. The Codex plugin is
# skills only (Markdown skills, reviewer personas and standards); it installs no hooks or executables.
# Usage: make_egm_home.sh <work dir, e.g. ~/code/benchmark/skills-impact-work>
set -euo pipefail
W="$1"; SRC="$W/home-clean"; H="$W/home-egm"
REF=d651fe86c12dccc5272274e002674fb8eec4c547
rm -rf "$H"; mkdir -p "$H/.codex"
cp "$SRC/.gitconfig" "$H/.gitconfig"
ln -s "$(readlink "$SRC/.m2")" "$H/.m2"
cp "$SRC/.codex/auth.json" "$H/.codex/auth.json"
: > "$H/.codex/config.toml"
HOME="$H" CODEX_HOME="$H/.codex" codex plugin marketplace add google/elephant-goldfish-model --ref "$REF"
HOME="$H" CODEX_HOME="$H/.codex" codex plugin add egm@egm
find "$H/.codex" -name SKILL.md | sed "s#^$H#~egm-home#"
echo "EGM home at $H"
