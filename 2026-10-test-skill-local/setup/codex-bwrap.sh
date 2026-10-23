#!/usr/bin/env bash
# Linux replacement for the rig's macOS-only `isolate`: runs `codex "$@"` inside bubblewrap.
# Allowlist: / is read-only; /home, /tmp and /run/user are empty tmpfs, so the experiments folder (hidden tests), the real
# home config (~/.codex, ~/.claude, ...) and every other run's folder are invisible. Bound back in:
#   - this run's work folder ($PWD, read-write)
#   - the Codex binary (read-only)
#   - a fresh per-run CODEX_HOME at ~/.codex (read-write, kept under $TRIAL_OUT/agent-homes/$TRIAL_ID for the rollout)
#   - ~/.m2/repository as an overlay with a tmpfs upper layer: Maven works offline, and anything the agent writes
#     (e.g. `mvn install`) disappears with the run, so the shared repository is never changed.
# The environment is cleared and rebuilt. The network is shared, because the model server is on 127.0.0.1.
# CODEX_PROFILE=hosted (calibration): OpenAI provider with the real login copied in, instead of the local model.
# CODEX_BIN overrides the program run inside the sandbox (used by isolation-test.sh to probe it).
# Usage (agent `command` in the toml): bash codex-bwrap.sh exec -s danger-full-access --skip-git-repo-check --json ... "{prompt}"
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"
U="$(getent passwd "$(id -u)" | cut -d: -f6)"   # real home, even if HOME was overridden
WORK="$(pwd -P)"
M2="$U/.m2/repository"
JDK=/usr/lib/jvm/java-21-openjdk-amd64

CH="${TRIAL_OUT:?TRIAL_OUT not set}/agent-homes/${TRIAL_ID:?TRIAL_ID not set}/.codex"
rm -rf "$CH"; mkdir -p "$CH"
# Optional seed (arm F, gate): its .codex contents (hooks.json and the gate scripts) are copied into the fresh home first.
if [ -n "${CODEX_SEED:-}" ]; then cp -R "$CODEX_SEED/.codex/." "$CH/"; fi
if [ "${CODEX_PROFILE:-local}" = hosted ]; then
  # Hosted calibration: as TSK's clean home, the login only and an empty config (OpenAI provider, built-in model catalog).
  cp "$U/.codex/auth.json" "$CH/auth.json"; : > "$CH/config.toml"
else
  cp "$L/codex-home/catalog.json" "$CH/catalog.json"
  sed "s#^model_catalog_json = .*#model_catalog_json = \"$U/.codex/catalog.json\"#" "$L/codex-home/config.toml" > "$CH/config.toml"
fi

exec bwrap \
  --ro-bind / / \
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
  --setenv LANG C.UTF-8 --setenv TERM dumb --setenv OLLAMA_API_KEY ollama \
  -- "${CODEX_BIN:-$L/codex-pkg/bin/codex}" "$@"
