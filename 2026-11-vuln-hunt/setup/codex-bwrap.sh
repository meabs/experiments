#!/usr/bin/env bash
# Runs hosted Codex (0.164, gpt-5.6-luna) inside bubblewrap for one review. Adapted from broken-tools' wrapper.
# Visible to the agent: / read-only; /home, /tmp and /run/user empty, so this experiments folder (the answer key and
# proof tests) and the real home are invisible. Bound back in: the run's workspace ($PWD, read-write), the Codex
# release (read-only), the run's Codex home at ~/.codex (read-write), and the target app's Python environment
# (read-only, first on PATH, so `python`, `pytest` and `flask` work as in a developer's checkout). The network is
# not cut off, because Codex reaches its model over it; web search is disabled in run.py.
set -euo pipefail
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
WORK="$(pwd -P)"
CODEX_REL="$(dirname "$(dirname "$(readlink -f "$U/.local/bin/codex")")")"
VENV="$U/code/benchmark/venvs/shopapi"
CH="${RUN_CODEX_HOME:?RUN_CODEX_HOME not set}"
if [ ! -f "$CH/auth.json" ]; then
  mkdir -p "$CH"; cp "$U/.codex/auth.json" "$CH/auth.json"; : > "$CH/config.toml"
fi
exec bwrap \
  --ro-bind / / \
  --dev /dev --proc /proc \
  --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --dir "$U" \
  --bind "$CH" "$U/.codex" \
  --ro-bind "$CODEX_REL" "$CODEX_REL" \
  --ro-bind "$VENV" "$VENV" \
  --bind "$WORK" "$WORK" \
  --chdir "$WORK" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent --new-session \
  --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv VIRTUAL_ENV "$VENV" --setenv PATH "$VENV/bin:/usr/bin:/bin" \
  --setenv LANG C.UTF-8 --setenv TERM dumb \
  -- "$CODEX_REL/bin/codex" "$@"
