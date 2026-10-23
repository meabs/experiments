#!/usr/bin/env bash
# Copies a finished stage into results/, with the home folder replaced by ~, the user and host names by placeholders,
# and large logs gzipped. Portable version of 2026-10-test-skill/scripts/export.sh (GNU or BSD sed, no `sed -i ''`).
# Usage: export.sh <stage dir> <results subfolder>
# Skips work/ (the clones), sandbox profiles and agent-homes/ (each run's Codex home, with the raw rollout). From each
# rollout it keeps only session.json: the model, provider, reasoning effort and Codex version the session actually used.
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$(cd "$1" && pwd)"; DST="$E/results/$2"
U="$(id -un)"; HOST="$(hostname -s)"; H="$HOME"
rm -rf "$DST"; mkdir -p "$DST"
rsync -a --exclude work --exclude agent-homes --exclude isolate.sb --exclude '*.orig' "$SRC/" "$DST/"
python3 -I - "$SRC" "$DST" <<'EOF'
import glob, json, os, re, sys
src, dst = sys.argv[1:]
for run in glob.glob(os.path.join(dst, "runs/*/*/*/*/run.json")):
    d = json.load(open(run))
    tid = re.sub(r"[^A-Za-z0-9]+", "_", f"{d['question']}_{d['arm']}_{d['agent']}_{d['rep']}").strip("_").lower()  # as the rig
    rolls = glob.glob(os.path.join(src, "agent-homes", tid, ".codex/sessions/*/*/*/*.jsonl"))
    out = {"rollouts": len(rolls), "turns": []}
    for r in rolls:
        for line in open(r):
            e = json.loads(line); p = e.get("payload", {})
            if e.get("type") == "session_meta":
                out.update(cli_version=p.get("cli_version"), model_provider=p.get("model_provider"), originator=p.get("originator"))
            elif e.get("type") == "turn_context":
                out["turns"].append({k: p.get(k) for k in ("model", "effort", "summary", "approval_policy", "sandbox_policy")})
            elif p.get("type") == "token_count" and p.get("info"):
                out["tokens"] = p["info"].get("total_token_usage")
    json.dump(out, open(os.path.join(os.path.dirname(run), "session.json"), "w"), indent=1)
EOF
scrub() { if sed --version >/dev/null 2>&1; then sed -i -E "$1" "$2"; else sed -i '' -E "$1" "$2"; fi; }
find "$DST" -type f \( -name '*.json' -o -name '*.log' -o -name '*.out' -o -name '*.err' -o -name '*.diff' -o -name '*.md' -o -name '*.csv' \) -print0 |
  while IFS= read -r -d '' f; do scrub "s#$H#~#g; s#$HOST(\\.local)?#host.local#g; s#home-$U-#home-USER-#g; s#$U#user#g" "$f"; done
find "$DST" -type f \( -name raw.out -o -name '*-mvn.log' -o -name 'relevance-*.log' \) -exec gzip -9 {} +
if grep -rIil -e "$H" -e "$U" -e "$HOST" "$DST"; then echo "personal path left in files above" >&2; exit 1; fi
find "$DST" -name '*.gz' -print0 | while IFS= read -r -d '' f; do
  if gzip -dc "$f" | grep -qi -e "$U" -e "$HOST"; then echo "personal path left in $f" >&2; exit 1; fi
done
du -sh "$DST"
