#!/usr/bin/env bash
# Builds the files arms S and O need. Needs network (once); the runs need none.
#   arms/S: Spec Kit (specify-cli 1.4.2) initialised for Codex, with the bug extension
#   arms/O: OpenSpec 2.1.0 initialised for Codex (project scope)
#   build/openspec: the OpenSpec command, bound read-only into the sandbox; build/codex-bwrap-sdd.sh: the shared
#   sandbox script with the PATH extended by $CODEX_EXTRA_PATH (the shared script is not edited).
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
B="$E/build"; mkdir -p "$B"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

rm -rf "$E/arms/S/.agents" "$E/arms/S/.specify" && mkdir -p "$T/S" && cd "$T/S" && git init -q .
uvx --from specify-cli==1.4.2 specify init --here --force --non-interactive --integration codex --integration-options="--skills" > /dev/null
uvx --from specify-cli==1.4.2 specify extension add bug > /dev/null
cp -R .agents .specify "$E/arms/S/"

rm -rf "$E/arms/O/.agents" "$E/arms/O/openspec" && mkdir -p "$T/O" && cd "$T/O" && git init -q .
npx -y @fission-ai/openspec@2.1.0 init --tools codex --scope project --no-animation > /dev/null
cp -R .agents openspec "$E/arms/O/"

npm install --silent --prefix "$B/openspec" @fission-ai/openspec@2.1.0

L=/home/garry/code/benchmark/local-setup
sed -e "s#^L=.*#L=\"$L\"#" \
    -e 's#--setenv PATH "\$JDK/bin:#--setenv PATH "${CODEX_EXTRA_PATH:+$CODEX_EXTRA_PATH:}$JDK/bin:#' \
    -e 's#--setenv LANG C.UTF-8#--setenv OPENSPEC_TELEMETRY 0 --setenv DO_NOT_TRACK 1 --setenv LANG C.UTF-8#' \
    "$L/codex-bwrap.sh" > "$B/codex-bwrap-sdd.sh"
grep -q CODEX_EXTRA_PATH "$B/codex-bwrap-sdd.sh" && grep -q "^L=\"$L\"" "$B/codex-bwrap-sdd.sh"
echo "built: arms/S arms/O build/openspec build/codex-bwrap-sdd.sh"
