#!/usr/bin/env bash
# Runs hosted Codex (gpt-5.6-luna) inside bubblewrap for one run. Copied from 2026-10-grilling, plus one change for
# broken-tools: /usr/local/bin is an empty tmpfs, and for the TRANS fault $FAULT_MVN (a Maven wrapper that fails once)
# is bound in as /usr/local/bin/mvn, ahead of /usr/bin/mvn on PATH.
# Original header: Runs hosted Codex (gpt-5.6-luna) inside bubblewrap for one turn of one run. Adapted from repo-injection's
# setup/codex-bwrap.sh, with two changes: no /etc/hosts replacement (nothing is planted), and the per-run Codex home
# ($RUN_CODEX_HOME) is kept between turns, so that `codex exec resume` finds the session.
# Visible to the agent: / read-only; /home, /tmp and /run/user empty, so this experiments folder (the hidden tests,
# the developer briefs, the references) and the real home are invisible. Bound back in: the run's workspace ($PWD,
# read-write), the Codex binary (read-only), the run's Codex home at ~/.codex (read-write), and ~/.m2/repository as an
# overlay with a throwaway upper layer.
set -euo pipefail
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
L="$U/code/benchmark/local-setup"
WORK="$(pwd -P)"
M2="$U/.m2/repository"
JDK=/usr/lib/jvm/java-21-openjdk-amd64
CH="${RUN_CODEX_HOME:?RUN_CODEX_HOME not set}"
if [ ! -f "$CH/auth.json" ]; then
  mkdir -p "$CH"; cp "$U/.codex/auth.json" "$CH/auth.json"; : > "$CH/config.toml"
fi
EXTRA=(--tmpfs /usr/local/bin)
if [ -n "${FAULT_MVN:-}" ]; then EXTRA+=(--ro-bind "$FAULT_MVN" /usr/local/bin/mvn); fi
exec bwrap \
  --ro-bind / / \
  --dev /dev --proc /proc \
  --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --dir "$U" \
  --ro-bind "$L/codex-pkg" "$L/codex-pkg" \
  --bind "$CH" "$U/.codex" \
  --overlay-src "$M2" --tmp-overlay "$M2" \
  --bind "$WORK" "$WORK" \
  "${EXTRA[@]}" \
  --chdir "$WORK" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent --new-session \
  --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv JAVA_HOME "$JDK" --setenv PATH "$JDK/bin:/usr/local/bin:/usr/bin:/bin" \
  --setenv LANG C.UTF-8 --setenv TERM dumb \
  -- "${CODEX_BIN:-$L/codex-pkg/bin/codex}" "$@"
