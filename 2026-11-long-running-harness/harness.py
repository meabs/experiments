#!/usr/bin/env python3
"""Multi-session coding-agent harness for the LRH experiment (stdlib only).

One run = one agent building tasks.py from SPEC.md across several short sessions. A session ends
when the agent stops calling tools, hits the turn cap, or its context passes the cap; the next
session starts with an empty conversation and only the working directory (files + git) carries over.
The four conditions differ only in prompt text and the starter files (see CONDITIONS).
"""
import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / 'runs'
WORK_ROOT = Path('/tmp/lrh-work')
KEY_FILE = Path.home() / '.config' / 'openrouter.key'
API = 'https://openrouter.ai/api/v1/chat/completions'
FEATURES = ['F%02d' % i for i in range(1, 13)]

SYSTEM = ('You are an autonomous coding agent working in a sandboxed directory. Use the tools to read, '
          'write and run code. Be concise; do not ask questions, nobody will answer.')

BASE = ('Implement tasks.py exactly as described in SPEC.md (Python 3 standard library only). The working '
        'directory is a git repository. Your work may span several sessions: a session ends without warning '
        'when its context or turn budget runs out, and the next session starts with no memory of this one; '
        'only the files and git history remain. When the entire spec is implemented and working, call '
        'declare_done.')

NOTES = ('\n\nAt the start of every session, read `git log` and PROGRESS.md (if they exist) to find out what '
         'was done. Before you finish, make sure the code runs, commit your work with a descriptive message, '
         'and append to PROGRESS.md what you did and what is next.')

FEATURELIST = ('\n\nfeature_list.json lists every feature with "passes": false. Work on exactly ONE feature '
               'per session: pick the highest-priority feature that is not yet passing. Edit '
               'feature_list.json only by changing the "passes" field of an entry; it is unacceptable to '
               'remove or edit entries, because that could lead to missing or buggy functionality. Commit '
               'after each feature.')

FULL = ('\n\nAt the start of every session run `sh init.sh` (it runs your tests and a basic end-to-end '
        'check) and fix anything broken before starting new work. Keep your own unittest tests in tests/. '
        'Only set "passes" to true after you have written a test for the feature and run it successfully.')

INIT_SH = """#!/bin/sh
# Basic end-to-end check, run at the start of every session.
if [ -d tests ]; then python3 -m unittest discover -s tests 2>&1 | tail -5; fi
d=$(mktemp -d); cp tasks.py "$d"/ 2>/dev/null || { echo "tasks.py missing"; exit 1; }
(cd "$d" && python3 tasks.py add smoke && python3 tasks.py list) && echo "smoke: ok" || echo "smoke: BROKEN"
"""

CONDITIONS = {
    'bare': BASE,
    'notes': BASE + NOTES,
    'featurelist': BASE + NOTES + FEATURELIST,
    'full': BASE + NOTES + FEATURELIST + FULL,
}

TOOLS = [
    {'type': 'function', 'function': {
        'name': 'bash', 'description': 'Run a shell command in the working directory (30s limit, no network).',
        'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'}}, 'required': ['command']}}},
    {'type': 'function', 'function': {
        'name': 'write_file', 'description': 'Write (overwrite) a text file, path relative to the working directory.',
        'parameters': {'type': 'object', 'properties': {'path': {'type': 'string'}, 'content': {'type': 'string'}},
                       'required': ['path', 'content']}}},
    {'type': 'function', 'function': {
        'name': 'read_file', 'description': 'Read a text file, path relative to the working directory.',
        'parameters': {'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path']}}},
    {'type': 'function', 'function': {
        'name': 'declare_done', 'description': 'Call when the entire spec is implemented and verified. Ends the run.',
        'parameters': {'type': 'object', 'properties': {}}}},
]

_ledger_lock = threading.Lock()


class BudgetExceeded(Exception):
    pass


def spent():
    p = RUNS / 'ledger.jsonl'
    if not p.exists():
        return 0.0
    return sum(json.loads(l)['cost'] for l in p.read_text().splitlines() if l.strip())


def charge(run_id, cost):
    with _ledger_lock:
        RUNS.mkdir(exist_ok=True)
        with open(RUNS / 'ledger.jsonl', 'a') as f:
            f.write(json.dumps({'run': run_id, 'cost': cost}) + '\n')


class OpenRouter:
    def __init__(self, model, budget):
        self.model, self.budget = model, budget
        self.key = KEY_FILE.read_text().strip()

    def chat(self, messages):
        if spent() >= self.budget:
            raise BudgetExceeded('spent %.2f >= cap %.2f' % (spent(), self.budget))
        body = {'model': self.model, 'messages': messages, 'tools': TOOLS, 'temperature': 0.7,
                'max_tokens': 3000, 'usage': {'include': True}}
        last = None
        for attempt in range(4):
            try:
                req = urllib.request.Request(API, json.dumps(body).encode(), {
                    'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=180) as r:
                    d = json.load(r)
                if 'choices' not in d:
                    raise RuntimeError(str(d)[:300])
                u = d.get('usage') or {}
                return {'message': d['choices'][0]['message'], 'prompt_tokens': u.get('prompt_tokens', 0),
                        'completion_tokens': u.get('completion_tokens', 0), 'cost': float(u.get('cost') or 0)}
            except (urllib.error.URLError, RuntimeError, TimeoutError, json.JSONDecodeError, OSError) as e:
                last = e
                if isinstance(e, urllib.error.HTTPError):
                    try:
                        last = '%s: %s' % (e, e.read()[:300].decode('utf-8', 'replace'))
                    except Exception:
                        pass
                time.sleep(2 * 2 ** attempt)
        raise RuntimeError('model call failed: %s' % last)


class Fake:
    """Scripted client for tests: a list of assistant messages, returned in order."""

    def __init__(self, script):
        self.script = list(script)

    def chat(self, messages):
        m = self.script.pop(0) if self.script else {'role': 'assistant', 'content': 'finished'}
        n = sum(len(json.dumps(x)) for x in messages) // 4
        return {'message': m, 'prompt_tokens': n, 'completion_tokens': 10, 'cost': 0.0}


def call(name, **args):
    return {'id': 'c%d' % time.monotonic_ns(), 'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(args)}}


def say(*calls, content=None):
    return {'role': 'assistant', 'content': content, 'tool_calls': list(calls)} if calls else \
        {'role': 'assistant', 'content': content or 'finished'}


# ---------------------------------------------------------------- sandbox and tools

def safe_path(work, rel):
    p = (work / rel).resolve()
    if work.resolve() not in p.parents and p != work.resolve():
        raise ValueError('path outside working directory')
    return p


def run_bash(work, command):
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/tmp', 'LANG': 'C.UTF-8',
           'GIT_AUTHOR_NAME': 'agent', 'GIT_AUTHOR_EMAIL': 'a@x', 'GIT_COMMITTER_NAME': 'agent',
           'GIT_COMMITTER_EMAIL': 'a@x'}
    if shutil.which('bwrap'):
        cmd = ['bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--proc', '/proc', '--tmpfs', '/tmp',
               '--tmpfs', '/home', '--tmpfs', '/root', '--bind', str(work), str(work), '--chdir', str(work),
               '--unshare-net', '--unshare-pid', '--die-with-parent', 'bash', '-c', command]
    else:
        cmd = ['bash', '-c', command]
    try:
        p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=30,
                           start_new_session=True)
        out = (p.stdout + p.stderr).strip()
        return ('%s\n[exit %d]' % (out, p.returncode))[-3000:]
    except subprocess.TimeoutExpired:
        return '[timed out after 30s]'


def execute(work, tc):
    name = tc['function']['name']
    try:
        a = json.loads(tc['function']['arguments'] or '{}')
        if name == 'bash':
            return run_bash(work, a['command'])
        if name == 'write_file':
            p = safe_path(work, a['path'])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(a['content'])
            return 'wrote %d bytes to %s' % (len(a['content']), a['path'])
        if name == 'read_file':
            return safe_path(work, a['path']).read_text()[:6000]
        if name == 'declare_done':
            return 'ok'
        return 'unknown tool: %s' % name
    except Exception as e:  # tool errors go back to the model
        return 'error: %s: %s' % (type(e).__name__, e)


# ---------------------------------------------------------------- scoring

def hidden_score(work):
    p = subprocess.run([sys.executable, str(HERE / 'hidden' / 'score.py'), str(work / 'tasks.py')],
                       capture_output=True, text=True, timeout=300)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {f: False for f in FEATURES}


def smoke_ok(work):
    t = work / 'tasks.py'
    if not t.exists():
        return False
    d = Path('/tmp') / ('lrh-smoke-%d' % time.monotonic_ns())
    d.mkdir()
    try:
        a = subprocess.run([sys.executable, str(t), 'add', 'smoke'], cwd=d, capture_output=True, text=True, timeout=20)
        b = subprocess.run([sys.executable, str(t), 'list'], cwd=d, capture_output=True, text=True, timeout=20)
        return a.returncode == 0 and b.returncode == 0 and 'smoke' in b.stdout
    except (subprocess.TimeoutExpired, OSError):
        return False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def feature_list_violations(work, original):
    """Count entries removed/added/altered other than the 'passes' field. Unparsable file = 1."""
    p = work / 'feature_list.json'
    try:
        cur = json.loads(p.read_text())
        if not isinstance(cur, list):
            return 1, {}
    except (OSError, json.JSONDecodeError):
        return 1, {}
    by_id = {e.get('id'): e for e in cur if isinstance(e, dict)}
    v = 0
    for o in original:
        c = by_id.get(o['id'])
        if c is None or {k: x for k, x in c.items() if k != 'passes'} != {k: x for k, x in o.items() if k != 'passes'}:
            v += 1
    v += len([e for e in cur if not (isinstance(e, dict) and e.get('id') in {o['id'] for o in original})])
    return v, {i: bool(e.get('passes')) for i, e in by_id.items()}


# ---------------------------------------------------------------- the run

def setup_workdir(condition, work):
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copy(HERE / 'spec' / 'SPEC.md', work / 'SPEC.md')
    if condition in ('featurelist', 'full'):
        shutil.copy(HERE / 'spec' / 'feature_list.json', work / 'feature_list.json')
    if condition == 'full':
        (work / 'init.sh').write_text(INIT_SH)
    env = dict(os.environ, GIT_AUTHOR_NAME='setup', GIT_AUTHOR_EMAIL='s@x', GIT_COMMITTER_NAME='setup',
               GIT_COMMITTER_EMAIL='s@x')
    for c in (['git', 'init', '-q'], ['git', 'add', '-A'], ['git', 'commit', '-qm', 'Initial commit']):
        subprocess.run(c, cwd=work, env=env, check=True, capture_output=True)


def run_one(client, condition, model_tag, rep, max_sessions=6, max_turns=40, ctx_limit=32000, out_root=None):
    run_id = '%s-%s-%d' % (model_tag, condition, rep)
    out = (out_root or RUNS) / run_id
    out.mkdir(parents=True, exist_ok=True)
    work = WORK_ROOT / run_id
    WORK_ROOT.mkdir(exist_ok=True)
    setup_workdir(condition, work)
    original = json.loads((HERE / 'spec' / 'feature_list.json').read_text())
    sessions, done, error = [], False, None
    tot = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0}
    log = open(out / 'transcript.jsonl', 'w')
    try:
        for s in range(1, max_sessions + 1):
            msgs = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': CONDITIONS[condition]}]
            reason, turns = 'turns', 0
            sess_tokens = 0
            for turns in range(1, max_turns + 1):
                r = client.chat(msgs)
                charge(run_id, r['cost'])
                for k in tot:
                    tot[k] += r[{'prompt_tokens': 'prompt_tokens', 'completion_tokens': 'completion_tokens',
                                 'cost': 'cost'}[k]]
                sess_tokens += r['prompt_tokens'] + r['completion_tokens']
                m = r['message']
                for tc in m.get('tool_calls') or []:
                    try:
                        json.loads(tc['function']['arguments'] or '{}')
                    except json.JSONDecodeError:
                        # The provider rejects the next request if bad arguments are echoed back.
                        tc['function']['arguments'] = '{}'
                        tc['bad_arguments'] = True
                msgs.append(m)
                log.write(json.dumps({'session': s, 'turn': turns, 'assistant': m}) + '\n')
                calls = m.get('tool_calls') or []
                if not calls:
                    reason = 'stopped'
                    break
                for tc in calls:
                    res = ('error: your tool call arguments were not valid JSON; call the tool again'
                           if tc.pop('bad_arguments', False) else execute(work, tc))
                    if tc['function']['name'] == 'declare_done':
                        done = True
                    msgs.append({'role': 'tool', 'tool_call_id': tc['id'], 'content': res})
                    log.write(json.dumps({'session': s, 'turn': turns, 'tool': tc['function']['name'],
                                          'result': res[:500]}) + '\n')
                log.flush()
                if done:
                    reason = 'declared_done'
                    break
                if r['prompt_tokens'] > ctx_limit:
                    reason = 'context'
                    break
            hidden = hidden_score(work)
            viol, claims = (feature_list_violations(work, original) if condition in ('featurelist', 'full')
                            else (0, {}))
            sessions.append({'session': s, 'turns': turns, 'reason': reason, 'passed': sum(hidden.values()),
                             'hidden': hidden, 'smoke_ok': smoke_ok(work), 'fl_violations': viol,
                             'claimed': sum(claims.values()),
                             'false_claims': sum(1 for f, c in claims.items() if c and not hidden.get(f)),
                             'tokens': sess_tokens})
            if done:
                break
    except BudgetExceeded as e:
        error = 'budget: %s' % e
    except Exception as e:
        error = '%s: %s' % (type(e).__name__, e)
    finally:
        log.close()
    final = sessions[-1]['passed'] if sessions else 0
    result = {'run_id': run_id, 'condition': condition, 'model': model_tag, 'rep': rep, 'error': error,
              'done_declared': done, 'final_passed': final, 'premature_victory': bool(done and final < 12),
              'sessions_used': len(sessions), 'broken_sessions': sum(1 for x in sessions if not x['smoke_ok']),
              'fl_violations': sum(x['fl_violations'] for x in sessions),
              'false_claims': sessions[-1]['false_claims'] if sessions else 0,
              'cost': round(tot['cost'], 5), 'prompt_tokens': tot['prompt_tokens'],
              'completion_tokens': tot['completion_tokens'], 'sessions': sessions,
              'limits': {'max_sessions': max_sessions, 'max_turns': max_turns, 'ctx_limit': ctx_limit}}
    (out / 'result.json').write_text(json.dumps(result, indent=1))
    dest = out / 'work'
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(work, dest)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--conditions', nargs='+', default=list(CONDITIONS), choices=list(CONDITIONS))
    ap.add_argument('--reps', type=int, default=1)
    ap.add_argument('--rep-start', type=int, default=1)
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--budget', type=float, default=8.0, help='stop when total ledger spend reaches this (USD)')
    ap.add_argument('--max-sessions', type=int, default=6)
    ap.add_argument('--max-turns', type=int, default=40)
    ap.add_argument('--ctx', type=int, default=32000)
    ap.add_argument('--redo-errors', action='store_true', help='rerun only runs whose result.json has an error')
    ap.add_argument('--regime', default='', help='suffix for run ids, e.g. tight')
    a = ap.parse_args()
    tag = a.model.replace('/', '_').replace(':', '_') + ('-' + a.regime if a.regime else '')
    client = OpenRouter(a.model, a.budget)
    jobs = [(c, r) for r in range(a.rep_start, a.rep_start + a.reps) for c in a.conditions]
    if a.redo_errors:
        def errored(c, r):
            f = RUNS / ('%s-%s-%d' % (tag, c, r)) / 'result.json'
            return f.exists() and json.loads(f.read_text()).get('error')
        jobs = [(c, r) for c, r in jobs if errored(c, r)]
        print('rerunning %d errored runs' % len(jobs), flush=True)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(run_one, client, c, tag, r, a.max_sessions, a.max_turns, a.ctx): (c, r) for c, r in jobs}
        for f in cf.as_completed(futs):
            r = f.result()
            print('%-28s passed %2d/12 sessions %d done=%s premature=%s cost=$%.4f %s' % (
                r['run_id'], r['final_passed'], r['sessions_used'], r['done_declared'], r['premature_victory'],
                r['cost'], r['error'] or ''), flush=True)
    print('total spent so far: $%.4f' % spent())


if __name__ == '__main__':
    main()
