"""Prints one line per Machinist job: id, recipe, title, state, stage and PR, from GET /api/v1/status."""
import json, subprocess, sys
M = __file__.rsplit('/', 1)[0] + '/mapi.sh'
d = json.loads(subprocess.run(['bash', M, 'GET', '/api/v1/status'], capture_output=True, text=True).stdout)
for j in d.get('jobs') or []:
    runs = j.get('runs') or []
    last = runs[-1] if runs else {}
    print(j['id'], j.get('recipe'), j.get('task', {}).get('title'), j.get('state'), f"runs={len(runs)}",
          last.get('command', ''), last.get('state', ''), j.get('workflow', {}).get('pr_url', '') or '')
