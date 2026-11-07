"""Per Machinist job: every Codex session it started (matched by the job ID in the session's working folder), the
models on every turn, tokens and cost at Luna's list price, and a leak scan for paths into the experiments folder.
Usage: python3 -I evidence.py JOB_ID [OUT.json]"""
import glob, json, os, re, sys

RT = os.path.expanduser('~/code/benchmark/asf-runtime/home')
PRICE = {'input': 0.20, 'cached': 0.02, 'output': 1.20}  # $ per million tokens, gpt-5.6-luna list price
OTHER_REPO = re.compile(r'(?<!users/)meabs/(?!asf-run-\d{3}\b)(?!asf-shopizer\b)([A-Za-z0-9_.-]+)')
LEAK = ('code/experiments', 'meabs/experiments', '/hidden/', 'HiddenOrderSupport', 'evidence-led', 'asf-1')

job = sys.argv[1]
out = {'job': job, 'sessions': [], 'models': {}, 'tokens': {'input': 0, 'cached': 0, 'output': 0}, 'leaks': []}
for f in sorted(glob.glob(f'{RT}/.codex/sessions/**/*.jsonl', recursive=True)):
    lines = open(f).read().splitlines()
    meta = json.loads(lines[0]).get('payload', {}) if lines else {}
    if job not in (meta.get('cwd') or ''):
        continue
    s = {'file': os.path.basename(f), 'models': {}, 'tokens': None}
    for l in lines:
        d = json.loads(l)
        p = d.get('payload', {})
        if d.get('type') == 'turn_context':
            m = f"{p.get('model')}@{p.get('effort')}"
            s['models'][m] = s['models'].get(m, 0) + 1
        if d.get('type') == 'event_msg' and p.get('type') == 'token_count' and p.get('info'):
            s['tokens'] = p['info']['total_token_usage']
        for k in LEAK:
            if k in l and d.get('type') != 'session_meta':
                out['leaks'].append({'file': s['file'], 'match': k})
        # any meabs repository other than a run repository (asf-run-NNN) or the old smoke repository
        if d.get('type') != 'session_meta':
            for m in OTHER_REPO.findall(l):
                out['leaks'].append({'file': s['file'], 'match': 'meabs/' + m})
    t = s['tokens'] or {}
    out['tokens']['input'] += t.get('input_tokens', 0)
    out['tokens']['cached'] += t.get('cached_input_tokens', 0)
    out['tokens']['output'] += t.get('output_tokens', 0)
    for m, n in s['models'].items():
        out['models'][m] = out['models'].get(m, 0) + n
    out['sessions'].append(s)
t = out['tokens']
out['cost_usd'] = round(((t['input'] - t['cached']) * PRICE['input'] + t['cached'] * PRICE['cached'] + t['output'] * PRICE['output']) / 1e6, 4)
out['luna_only'] = bool(out['models']) and set(out['models']) == {'gpt-5.6-luna@medium'}
print(json.dumps({k: v for k, v in out.items() if k != 'sessions'} | {'n_sessions': len(out['sessions'])}, indent=1))
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
