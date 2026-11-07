#!/usr/bin/env bash
# Runs a Machinist command (init, start, ...) inside bubblewrap, so Machinist and every Codex agent it starts
# (Machinist runs them with --sandbox danger-full-access) cannot see the real home: /home, /tmp and /run/user are
# empty, and the real home path is replaced by the ASF runtime home ($ASF_RT/home). The hidden tests, the experiments
# folder, ~/.codex and ~/.config stay invisible. Bound in:
#   - the runtime home (read-write): .machinist (config, jobs.db, checkouts), .codex (login copy + pinned Luna config)
#   - Codex 0.157.0 (the rig's codex-pkg, the same build as arm A) and the Machinist binary, read-only under ~/opt
#   - ~/.m2/repository as an overlay with a tmpfs upper layer (shared cache; writes vanish when the sandbox stops)
# The network is shared: Machinist needs GitHub and the browser reaches its UI on 127.0.0.1:7331.
# Usage: ASF_RT=~/code/benchmark/asf-runtime bash machinist-sandbox.sh start
# ASF_EXEC overrides the program run inside (the isolation check runs bash).
set -euo pipefail
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
RT="${ASF_RT:-$U/code/benchmark/asf-runtime}"
H="$RT/home"
PKG="$U/code/benchmark/local-setup/codex-pkg"
MBIN="$U/code/machinist/bin"
M2="$U/.m2/repository"
JDK=/usr/lib/jvm/java-21-openjdk-amd64
mkdir -p "$H/.codex" "$H/.m2/repository" "$H/bin" "$H/opt/codex-pkg" "$H/opt/machinist"
# `codex` inside the sandbox is a wrapper: it pins Luna at medium effort on every exec and app-server call (Machinist's
# connection check uses app-server, which ignored config.toml's model and ran gpt-6-astra) and logs each argv.
cat > "$H/bin/codex" <<'WRAP'
#!/bin/sh
REAL="$HOME/opt/codex-pkg/bin/codex"
printf '%s %s\n' "$(date -Is)" "$*" >> "$HOME/codex-invocations.log"
case "$1" in
  exec|app-server) sub="$1"; shift; exec "$REAL" "$sub" -c 'model="gpt-5.6-luna"' -c 'model_reasoning_effort="medium"' "$@" ;;
  *) exec "$REAL" "$@" ;;
esac
WRAP
chmod 755 "$H/bin/codex"
ln -sfn $U/opt/machinist/machinist "$H/bin/machinist"
exec bwrap \
  --ro-bind / / \
  --dev /dev --proc /proc \
  --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --bind "$H" "$U" \
  --ro-bind "$PKG" $U/opt/codex-pkg \
  --ro-bind "$MBIN" $U/opt/machinist \
  --overlay-src "$M2" --tmp-overlay "$U/.m2/repository" \
  --chdir "$U" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent \
  --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv JAVA_HOME "$JDK" --setenv PATH "$U/bin:$JDK/bin:/usr/local/bin:/usr/bin:/bin" \
  --setenv LANG C.UTF-8 --setenv TERM dumb \
  -- ${ASF_EXEC:-$U/opt/machinist/machinist} "$@"
