#!/usr/bin/env bash
# Copies a finished run into results/<name>, portable (GNU or BSD sed). Usage: export.sh <out dir> <results subfolder>
# Keeps each answer's result.json, raw.out (Codex events, gzipped) and raw.err, plus power.csv. Leaves out work/ and
# agent-homes/ (each answer's Codex home: the raw rollout and, for the hosted model, the login). From each rollout it
# keeps session.json: the model, provider, reasoning effort and Codex version the session actually used.
# Replaces the home folder with ~ and the user and host names with placeholders; fails if any is left, also inside .gz files.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$(cd "$1" && pwd)"; DST="$E/results/$2"
U="$(id -un)"; HOST="$(hostname -s)"; H="$HOME"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a --exclude work --exclude agent-homes "$SRC/" "$DST/"
python3 -I - "$SRC" "$DST" <<'PY'
import glob, json, os, re, sys
src, dst = sys.argv[1:]
for f in glob.glob(os.path.join(dst, "*", "*", "*", "*", "result.json")):
    group, bench, var, idx = f.split(os.sep)[-5:-1]
    tid = f"{bench}_{var}_{idx}"
    out = {"rollouts": 0, "turns": []}
    for r in glob.glob(os.path.join(src, group, "agent-homes", tid, ".codex/sessions/*/*/*/*.jsonl")):
        out["rollouts"] += 1
        for line in open(r):
            e = json.loads(line); p = e.get("payload", {})
            if e.get("type") == "session_meta":
                out.update(cli_version=p.get("cli_version"), model_provider=p.get("model_provider"))
            elif e.get("type") == "turn_context":
                out["turns"].append({k: p.get(k) for k in ("model", "effort", "sandbox_policy")})
    json.dump(out, open(os.path.join(os.path.dirname(f), "session.json"), "w"), indent=1)
PY
scrub() { if sed --version >/dev/null 2>&1; then sed -i -E "$1" "$2"; else sed -i '' -E "$1" "$2"; fi; }
find "$DST" -type f \( -name '*.json' -o -name '*.out' -o -name '*.err' -o -name '*.md' -o -name '*.csv' -o -name '*.log' \) -print0 |
  while IFS= read -r -d '' f; do scrub "s#$H#~#g; s#$HOST(\\.local)?#host.local#g; s#home-$U-#home-USER-#g; s#$U#user#g" "$f"; done
find "$DST" -type f -name raw.out -exec gzip -9 {} +
if grep -rIil -e "$H" -e "$U" -e "$HOST" "$DST"; then echo "personal path left in files above" >&2; exit 1; fi
find "$DST" -name '*.gz' -print0 | while IFS= read -r -d '' f; do
  if gzip -dc "$f" | grep -qi -e "$U" -e "$HOST"; then echo "personal path left in $f" >&2; exit 1; fi
done
du -sh "$DST"
