#!/usr/bin/env bash
# Linux + local-model localization for one experiment folder (default 2026-10-test-skill).
# 1. runs the experiment's own scripts/localize.sh (/Users/USER -> $HOME) to write trial*.local.toml
# 2. rewrites the [[agents]] block for the local model: codex runs through codex-bwrap.sh (bubblewrap isolation, clean
#    per-run HOME/CODEX_HOME, throwaway Maven overlay), the model is qwen3.8:27b, and the rig's macOS-only `isolate` is emptied
# 3. sets parallel = 1 (one GPU, one Ollama slot); timeouts stay as designed (1800 s, gate 2700 s)
# 4. writes scripts/verify.local.sh and scripts/relevance.local.sh with the Linux JDK in place of /opt/homebrew/opt/openjdk@21
# 5. builds local-setup/gate-seed: arm F's hooks.json and gate scripts (Linux JDK), copied into each gate run's fresh CODEX_HOME
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"
E="${1:-$HOME/code/experiments/2026-10-test-skill}"
JDK=/usr/lib/jvm/java-21-openjdk-amd64
bash "$E/scripts/localize.sh"
for s in verify relevance; do
  sed -e "s#/opt/homebrew/opt/openjdk@21#$JDK#g" -e 's#scripts/relevance\.sh#scripts/relevance.local.sh#g' "$E/scripts/$s.sh" > "$E/scripts/$s.local.sh"
done
G="$L/gate-seed/.codex"; rm -rf "$L/gate-seed"; mkdir -p "$G/gate"
cp "$E/scripts/gate.sh" "$E/scripts/relevance.py" "$G/gate/"; cp "$E/scripts/relevance.local.sh" "$G/gate/relevance.sh"; chmod +x "$G/gate/"*.sh
printf '{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "%s/.codex/gate/gate.sh", "timeout": 900}]}]}}\n' "$HOME" > "$G/hooks.json"
for f in trial trial-medium trial-gate; do
  python3 -I - "$E/$f.local.toml" "$L" "$JDK" <<'EOF'
import re, sys, json, tomllib
p, L, jdk = sys.argv[1:]
s = open(p).read()
m = re.search(r'^\[\[agents\]\]\n(.*?)(?=^\[\[|\Z)', s, re.S | re.M)
old = tomllib.loads("[[agents]]\n" + m.group(1))["agents"][0]
model = "qwen3.8:27b"
cmd = ["bash", f"{L}/codex-bwrap.sh", "exec", "-s", "danger-full-access", "--skip-git-repo-check", "--json", "--model", model, *old["args"], "{prompt}"]
q = lambda v: json.dumps(v)
seed = f', CODEX_SEED = {q(L + "/gate-seed")}' if 'home-gate' in m.group(1) else ''
block = (f'[[agents]]\nname = {q(old["name"])}\n'
         f'# local model via Ollama; codex runs inside bubblewrap (codex-bwrap.sh) since `isolate` is macOS-only\n'
         f'model = {q(model)}\ncommand = [{", ".join(map(q, cmd))}]\nargs = []\nedits = true\nsandbox = "danger-full-access"\n'
         f'env = {{ JAVA_HOME = {q(jdk)}, PATH = {q(jdk + "/bin:/usr/local/bin:/usr/bin:/bin")}{seed} }}\nisolate = []\n\n')
s = s[:m.start()] + block + s[m.end():]
s = re.sub(r'^parallel = \d+', 'parallel = 1', s, flags=re.M)
s = s.replace("scripts/verify.sh", "scripts/verify.local.sh")
s = "# LOCALIZED by local-setup/localize-linux.sh for the local-model rerun (Linux, qwen3.8:27b via Ollama).\n" + s
t = tomllib.loads(s)  # must still parse
assert all(a["isolate"] == [] and a["command"][1].endswith("codex-bwrap.sh") for a in t["agents"])
assert "/Users/" not in s and "homebrew" not in s, "mac path left"
open(p, "w").write(s)
print(f"{p}: {len(t['questions'])} tasks, {len(t['arms'])} arms, reps {t['defaults']['reps']}, agent args {old['args']}")
EOF
done
grep -l homebrew "$E"/scripts/*.local.sh && { echo "homebrew path left"; exit 1; } || true
