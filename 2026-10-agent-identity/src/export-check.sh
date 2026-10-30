#!/usr/bin/env bash
# Fails if anything under results/ holds a personal path, the user name, or a credential from setup/local-secrets.json.
# (The results are published as written; no transformation is needed. Portable: no BSD sed -i ''.)
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
U="$(getent passwd "$(id -u)" | cut -d: -f6)"
PATTERNS=("$U" "$(id -un)@")
if [ -f "$E/setup/local-secrets.json" ]; then
  while read -r s; do PATTERNS+=("$s"); done < <(python3 -c "import json,sys; print('\n'.join(json.load(open(sys.argv[1])).values()))" "$E/setup/local-secrets.json")
fi
for p in "${PATTERNS[@]}"; do
  if grep -rqF -- "$p" "$E/results"; then echo "found a personal path or credential in results/" >&2; exit 1; fi
done
echo "results/ clean: $(find "$E/results" -type f | wc -l) files"
