#!/usr/bin/env bash
# Builds arms/superpowers from the pinned upstream commit, exactly as in skills-tasks. Third-party contents are not
# committed. arms/verify (the arm B instruction) is committed as written in the README.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="${PACK_CACHE:-$HOME/code/benchmark/skills-impact-work/packs}"
mkdir -p "$CACHE"
SP=b739a8af570e10a95898f2bdf6cec97467fa6c12
d="$CACHE/superpowers"
[ -d "$d/.git" ] || git clone -q https://github.com/obra/superpowers "$d"
git -C "$d" fetch -q --depth 1 origin $SP 2>/dev/null || true
git -C "$d" checkout -q $SP
A="$E/arms/superpowers"; rm -rf "$A"; mkdir -p "$A/.agents/skills"
cp -R "$d/skills/." "$A/.agents/skills/"
{ printf '<EXTREMELY_IMPORTANT>\nYou have superpowers.\n\n**Below is the full content of your '"'"'superpowers:using-superpowers'"'"' skill - your introduction to using skills. For all other skills, use the '"'"'Skill'"'"' tool:**\n\n'
  cat "$d/skills/using-superpowers/SKILL.md"
  printf '\n</EXTREMELY_IMPORTANT>\n'; } > "$A/AGENTS.md"
echo "obra/superpowers $SP (all skills; sessionStart hook text in AGENTS.md)" > "$A/SOURCE"
for a in verify superpowers; do printf '%-12s %s files\n' $a "$(find "$E/arms/$a" -type f | wc -l | tr -d ' ')"; done
