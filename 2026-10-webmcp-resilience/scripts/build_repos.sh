#!/usr/bin/env bash
# Builds one git repository per task app under $WEBMCP_WORK/repos (default ~/code/benchmark/webmcp-exp), from apps/.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
X="${WEBMCP_WORK:-$HOME/code/benchmark/webmcp-exp}"
for d in "$E"/apps/*/; do
  t="$(basename "$d")"; [ "$t" = _shared ] && continue
  r="$X/repos/$t"; rm -rf "$r"; mkdir -p "$r"; cp -r "$d". "$r/"
  git -C "$r" init -q && git -C "$r" -c user.name=trial -c user.email=trial@example.com add -A
  git -C "$r" -c user.name=trial -c user.email=trial@example.com commit -q -m "$t"
  echo "$r $(git -C "$r" rev-parse --short HEAD)"
done
