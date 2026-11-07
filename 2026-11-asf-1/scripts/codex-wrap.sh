#!/usr/bin/env bash
# The `codex` Machinist calls (first on its PATH; machinist-host.sh). Every Codex session Machinist starts runs here,
# each in its own bubblewrap sandbox, as arm A's rig does:
#   - / read-only; /home, /tmp, /run/user empty: the experiments folder (hidden tests), the real ~/.codex and
#     ~/.config, and Machinist's own state are invisible;
#   - bound in: the job's workspace (its cwd) and the checkout's shared .git; the Machinist run folders named in its
#     MACHINIST_*_PATH/_DIR variables; the ASF Codex home (login copy, sessions kept as evidence); Codex 0.157.0
#     and gh 2.103.3 read-only; ~/.m2/repository as an overlay with a tmpfs upper layer (fresh per call);
#   - a read-only role (`--sandbox read-only`, or sandbox_mode='read-only' for app-server) gets the workspace and .git
#     read-only. Codex's own read-only sandbox (bubblewrap) cannot start inside this one (Ubuntu's AppArmor userns
#     rule), so Codex runs with danger-full-access and this layer enforces the read-only part. Tool commands keep
#     network access, which Codex's read-only mode would have blocked (amendment log);
#   - Luna at medium effort pinned on every exec and app-server call; each call is logged with its argv and mode.
# Only GitHub and Machinist variables (GH_*, GITHUB_TOKEN, GIT_*, MACHINIST_*) pass into the sandbox.
set -euo pipefail
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
RT="$U/code/benchmark/asf-runtime"
PKG="$U/code/benchmark/local-setup/codex-pkg"
M2="$U/.m2/repository"
JDK=/usr/lib/jvm/java-21-openjdk-amd64
GH="$U/.local/gh-2.103.3"   # same gh as Machinist, so agents and Machinist see one version
WORK="$(pwd -P)"

mode=rw; args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --sandbox|-s) if [ "${2:-}" = read-only ]; then mode=ro; fi; args+=("$1" danger-full-access); shift 2; continue ;;
    --sandbox=read-only) mode=ro; args+=(--sandbox=danger-full-access) ;;
    "sandbox_mode='read-only'") mode=ro; args+=("sandbox_mode='danger-full-access'") ;;
    *) args+=("$1") ;;
  esac
  shift
done
sub="${args[0]:-}"
if [ "$sub" = exec ] || [ "$sub" = app-server ]; then
  args=("$sub" -c 'model="gpt-5.6-luna"' -c 'model_reasoning_effort="medium"' "${args[@]:1}")
fi
printf '%s mode=%s cwd=%s argv=%s\n' "$(date -Is)" "$mode" "$WORK" "${args[*]}" >> "$RT/codex-invocations.log"

B=(--bind); [ "$mode" = ro ] && B=(--ro-bind)
EXTRA=("${B[@]}" "$WORK" "$WORK")
if [ -f "$WORK/.git" ] || [ -d "$WORK/.git" ]; then
  common="$(git -C "$WORK" rev-parse --path-format=absolute --git-common-dir)"
  case "$common" in "$WORK"/*) ;; *) EXTRA+=("${B[@]}" "$common" "$common") ;; esac
fi
ENVS=()
while IFS= read -r -d '' kv; do
  name="${kv%%=*}"; val="${kv#*=}"
  case "$name" in
    GH_*|GITHUB_TOKEN|GIT_*|MACHINIST_*)
      ENVS+=(--setenv "$name" "$val")
      case "$name" in
        MACHINIST_*_PATH) d="$(dirname "$val")"; mkdir -p "$d"; EXTRA+=(--bind "$d" "$d") ;;
        MACHINIST_*_DIR) mkdir -p "$val"; EXTRA+=(--bind "$val" "$val") ;;
      esac ;;
  esac
done < <(env -0)

exec bwrap \
  --ro-bind / / \
  --dev /dev --proc /proc \
  --tmpfs /tmp --tmpfs /home --tmpfs /run/user \
  --dir "$U" \
  --ro-bind "$PKG" "$PKG" \
  --ro-bind "$GH" "$GH" \
  --bind "$RT/home/.codex" "$U/.codex" \
  --overlay-src "$M2" --tmp-overlay "$M2" \
  "${EXTRA[@]}" \
  --chdir "$WORK" \
  --unshare-pid --unshare-ipc --unshare-uts --die-with-parent \
  --clearenv \
  --setenv HOME "$U" --setenv USER "$(id -un)" --setenv CODEX_HOME "$U/.codex" \
  --setenv JAVA_HOME "$JDK" --setenv PATH "$GH/bin:$JDK/bin:/usr/local/bin:/usr/bin:/bin" \
  --setenv LANG C.UTF-8 --setenv TERM dumb \
  "${ENVS[@]}" \
  -- "${ASF_EXEC:-$PKG/bin/codex}" "${args[@]}"
