#!/usr/bin/env bash
# Tool-calling check: codex exec must read calc.py, edit it, run python. Usage: toolcheck.sh <workdir>
set -u; W=$1; L=$(cd "$(dirname "$0")" && pwd)
rm -rf "$W"; mkdir -p "$W"; cd "$W"; git init -q; printf 'def add(a, b):\n    return a - b\n' > calc.py
CODEX_HOME=$L/codex-home OLLAMA_API_KEY=ollama "$L/codex-pkg/bin/codex" exec --json -s workspace-write --skip-git-repo-check \
  "Read calc.py, fix the bug in add so it returns the sum, then run: python3 -c 'import calc; print(calc.add(2,3))' and report the output." \
  > events.jsonl 2> stderr.txt < /dev/null; echo "codex exit $?"
python3 -I -c "
import json
for l in open('events.jsonl'):
    e=json.loads(l); it=e.get('item',{})
    if e['type'] in('item.completed','turn.completed','turn.failed','error') and it.get('type')!='reasoning':
        print(e['type'], it.get('type',''), (it.get('command') or str(it.get('changes','')) or it.get('message') or it.get('text') or '')[:110].replace(chr(10),' '), it.get('exit_code',''), e.get('usage',''), e.get('error',''))
"
echo "calc.py: $(grep return calc.py)"; python3 -c 'import calc; print("check add(2,3) =", calc.add(2,3))'
