#!/usr/bin/env bash
# Builds arms/{superpowers,pocock,pstack} from pinned upstream commits. Third-party contents are not committed.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="${PACK_CACHE:-$HOME/code/benchmark/skills-impact-work/packs}"
mkdir -p "$CACHE"

fetch() { # repo commit dir
  local d="$CACHE/$3"
  [ -d "$d/.git" ] || git clone -q "https://github.com/$1" "$d"
  git -C "$d" fetch -q --depth 1 origin "$2" 2>/dev/null || true
  git -C "$d" checkout -q "$2"
  echo "$1 $2" 
}

SP=b739a8af570e10a95898f2bdf6cec97467fa6c12
MP=5beb35b040e3de97e54fa9e386d7e42d15c295c2
CP=190d28736eff128ec94f502a22c7fe0c4b56cd37

# superpowers: every skill, plus the text its sessionStart hook injects, delivered through AGENTS.md
A="$E/arms/superpowers"; rm -rf "$A"; mkdir -p "$A/.agents/skills"
fetch obra/superpowers $SP superpowers > /dev/null
cp -R "$CACHE/superpowers/skills/." "$A/.agents/skills/"
{ printf '<EXTREMELY_IMPORTANT>\nYou have superpowers.\n\n**Below is the full content of your '"'"'superpowers:using-superpowers'"'"' skill - your introduction to using skills. For all other skills, use the '"'"'Skill'"'"' tool:**\n\n'
  cat "$CACHE/superpowers/skills/using-superpowers/SKILL.md"
  printf '\n</EXTREMELY_IMPORTANT>\n'; } > "$A/AGENTS.md"
echo "obra/superpowers $SP (all skills; sessionStart hook text in AGENTS.md)" > "$A/SOURCE"

# pocock: exactly the skills listed in the plugin manifest
A="$E/arms/pocock"; rm -rf "$A"; mkdir -p "$A/.agents/skills"
fetch mattpocock/skills $MP mattpocock > /dev/null
python3 -c "import json,sys;[print(s) for s in json.load(open(sys.argv[1]))['skills']]" "$CACHE/mattpocock/.claude-plugin/plugin.json" |
  while read -r s; do cp -R "$CACHE/mattpocock/$s" "$A/.agents/skills/"; done
echo "mattpocock/skills $MP (skills from .claude-plugin/plugin.json)" > "$A/SOURCE"

# pstack: skills and agents as project-level Cursor files, every model role set to inherit-parent
A="$E/arms/pstack"; rm -rf "$A"; mkdir -p "$A/.cursor/skills" "$A/.cursor/agents" "$A/.cursor/rules"
fetch cursor/plugins $CP cursor-plugins > /dev/null
cp -R "$CACHE/cursor-plugins/pstack/skills/." "$A/.cursor/skills/"
cp -R "$CACHE/cursor-plugins/pstack/agents/." "$A/.cursor/agents/"
roles="feature, refactoring|bug-fix|perf-issue|hillclimb|judgment and prose|hardest tasks|how explorer|how explainer|why investigators|why synthesizer|reflect tooling|reflect judgment, divergent, synthesizer|swarm workers"
panels="arena runners|arena cross-judge pool|architect runners|interrogate reviewers"
{ printf -- '---\ndescription: pstack per-role model choices (overrides skill defaults)\nalwaysApply: true\n---\n'
  printf '# pstack model configuration. One line per role. Delete a line to fall back to the skill default.\n'
  printf '# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit Task `model`). Alias entries in a panel list still count toward its fan-out.\n'
  printf '# budget: experiment (every role on the parent model)\n'
  IFS='|'; for r in $roles; do printf '%s: inherit-parent\n' "$r"; done
  for r in $panels; do printf '%s: inherit-parent, inherit-parent\n' "$r"; done; } > "$A/.cursor/rules/pstack-models.mdc"
echo "cursor/plugins $CP pstack 0.15.29 (skills + agents project-level; all roles inherit-parent, panels keep two entries)" > "$A/SOURCE"

for a in placebo superpowers pocock pstack; do printf '%-12s %s files\n' $a "$(find "$E/arms/$a" -type f | wc -l | tr -d ' ')"; done
