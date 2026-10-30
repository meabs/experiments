#!/usr/bin/env bash
# Runs hosted Codex (gpt-5.6-luna) inside bubblewrap for one run. Adapted from ~/code/benchmark/local-setup/codex-bwrap.sh
# (sec-authz) with one addition: /etc/hosts is replaced by setup/hosts, which points the attacker's host name
# (audit.platform.internal) at this machine, where scripts/listener.py records every request. Nothing planted in the
# repository can reach a real outside host: the name only exists in this file, and `.internal` is reserved for private use.
# Visible to the agent: / read-only; /home, /tmp and /run/user empty, so this experiments folder (the hidden tests, the
# listener's log) and the real home are invisible. Bound back in: the run's work folder ($PWD, read-write), the Codex
# binary (read-only), a fresh per-run CODEX_HOME at ~/.codex (read-write; holds the login copy and the session file), and
# ~/.m2/repository as an overlay with a throwaway upper layer.
# The network is shared (the model is hosted). Codex's own sandbox can't be nested here: AppArmor
# (kernel.apparmor_restrict_unprivileged_userns=1) stops bubblewrap creating a namespace inside another one.
# CODEX_BIN overrides the program run inside the sandbox (scripts/isolation-test.sh uses it to probe).
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
U="$(getent passwd "$(id -u)" | cut -d: -f6)"   # real home, even if HOME was overridden
L="$U/code/benchmark/local-setup"
WORK="$(pwd -P)"
M2="$U/.m2/repository"
JDK=/usr/lib/jvm/java-21-openjdk-amd64

CH="${TRIAL_OUT:?TRIAL_OUT not set}/agent-homes/${TRIAL_ID:?TRIAL_ID not set}/.codex"
rm -rf "$CH"; mkdir -p "$CH"
cp "$U/.codex/auth.json" "$CH/auth.json"; : > "$CH/config.toml"

exec bwrap \
  --ro-bind / / \
  --ro-bind "$H/hosts" /etc/hosts \
  --dev /dev --proc /proc \
  --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --dir "$U" \
  --ro-bind "$L/codex-pkg" "$L/codex-pkg" \
  --bind "$CH" "$U/.codex" \
  --overlay-src "$M2" --tmp-overlay "$M2" \
  --bind "$WORK" "$WORK" \
  --chdir "$WORK" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent --new-session \
  --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv JAVA_HOME "$JDK" --setenv PATH "$JDK/bin:/usr/local/bin:/usr/bin:/bin" \
  --setenv LANG C.UTF-8 --setenv TERM dumb \
  -- "${CODEX_BIN:-$L/codex-pkg/bin/codex}" "$@"
