#!/usr/bin/env bash
# Runs hosted Codex (gpt-5.6-luna) inside bubblewrap for one agent run. Copied from 2026-10-team-herding/setup.
# Visible to the agent: / read-only; /home, /tmp and /run/user empty, so this experiments folder (with the services,
# the shared key and the client secrets) is invisible. Bound back in: the run's work folder ($PWD, read-write), the
# Codex binary (read-only), and the agent's own CODEX_HOME at ~/.codex (read-write; holds the login and the rollout).
# The network is shared, so the agent reaches its tool server on 127.0.0.1 (it could also reach the services directly,
# but holds no credentials for them).
# ACME_MCP_TOKEN (hardening follow-up): the tool server's per-session token, passed through so Codex can present it.
# CODEX_BIN overrides the program run inside the sandbox (setup/isolation-test.sh uses it to probe).
# Usage: AGENT_HOME=<dir> bash codex-bwrap.sh exec ...    (AGENT_HOME is created and seeded with the login if missing)
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
WORK="$(pwd -P)"
PKG="$U/code/benchmark/local-setup/codex-pkg"
CH="${AGENT_HOME:?AGENT_HOME not set}"
if [ ! -f "$CH/auth.json" ]; then
  mkdir -p "$CH"; cp "$U/.codex/auth.json" "$CH/auth.json"; : > "$CH/config.toml"
fi
exec bwrap \
  --ro-bind / / \
  --dev /dev --proc /proc \
  --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --dir "$U" \
  --ro-bind "$PKG" "$PKG" \
  --bind "$CH" "$U/.codex" \
  --bind "$WORK" "$WORK" \
  --chdir "$WORK" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent --new-session \
  --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv PATH "/usr/local/bin:/usr/bin:/bin" --setenv LANG C.UTF-8 --setenv TERM dumb \
  --setenv ACME_MCP_TOKEN "${ACME_MCP_TOKEN:-}" \
  -- "${CODEX_BIN:-$PKG/bin/codex}" "$@"
