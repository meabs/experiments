#!/usr/bin/env bash
# Starts Machinist's control plane on the host (state in ~/.machinist) with codex-wrap.sh as the only `codex` on
# its PATH, so every agent session it starts is sandboxed (see codex-wrap.sh). Machinist itself is not an agent.
set -euo pipefail
X="$(cd "$(dirname "$0")" && pwd)"
RT="$HOME/code/benchmark/asf-runtime"
mkdir -p "$RT/bin"; ln -sfn "$X/codex-wrap.sh" "$RT/bin/codex"
# gh 2.103.3 (Machinist calls `gh api --slurp`, which Ubuntu's gh 2.46 lacks); the system gh is untouched
ln -sfn "$HOME/.local/gh-2.103.3/bin/gh" "$RT/bin/gh"
export PATH="$RT/bin:$HOME/code/machinist/bin:/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/local/bin:/usr/bin:/bin"
exec "$HOME/code/machinist/bin/machinist" "$@"
