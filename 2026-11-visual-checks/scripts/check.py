"""Runs the checkers on screenshots and saves every raw answer.

  python3 -I check.py <shots dir> <checker> [--reps N] [--only id,id]     writes results/raw/<checker>/<shot>.r<k>.json

Screenshots: <shots dir>/clean/<screen>-<viewport>.png and <shots dir>/variants/<variant>/<screen>-<viewport>.png.
Checkers:
  pixel                   share of pixels that differ (any channel by more than 16) from the clean shot of that screen
  jev-assert              Jev (jev-latest), the screen's assertions as noul questions in one request
  jev-open                Jev, one noul: "Does this screenshot show a visual defect a customer would notice?"
  vlm-assert:<model>      an OpenRouter or Ollama vision model, the same assertions, answered yes/no as JSON
  vlm-review:<model>      the model reviews the screenshot and lists defects as JSON
<model> is an OpenRouter id (e.g. google/gemini-4-argon) or ollama/<name> for a local model.
Keys: ~/.config/jev.key, ~/.config/openrouter.key (never printed or saved with results).
"""
import base64, glob, io, json, os, re, sys, time, urllib.request

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSERT = json.load(open(os.path.join(E, 'assertions', 'assertions.json')))
VARIANTS = {v['id']: v for v in json.load(open(os.path.join(E, 'variants', 'variants.json')))}
OPEN_Q = 'Does this screenshot show a visual defect a customer would notice?'
REVIEW = ('You are reviewing a screenshot of an online shop for visual defects that a customer would notice: anything '
          'broken, hidden, covered, cut off, overlapping, unreadable, missing, inconsistent or wrong. Ordinary design '
          'choices (colours, fonts, spacing, layout, banners, picture choice, order of items) are not defects. Answer '
          'with JSON only: {"defects": ["short description", ...]} (an empty list if there are none).')


def key(name):
    return open(os.path.expanduser(f'~/.config/{name}.key')).read().strip()


def shots(root):
    out = []
    for p in sorted(glob.glob(os.path.join(root, 'clean', '*.png'))):
        screen, vp = os.path.basename(p)[:-4].split('-')
        out.append({'id': f'clean__{screen}-{vp}', 'path': p, 'screen': screen, 'viewport': vp, 'group': 'clean', 'variant': ''})
    for p in sorted(glob.glob(os.path.join(root, 'variants', '*', '*.png'))):
        vid = os.path.basename(os.path.dirname(p))
        if vid not in VARIANTS:
            continue
        screen, vp = os.path.basename(p)[:-4].split('-')
        out.append({'id': f'{vid}__{screen}-{vp}', 'path': p, 'screen': screen, 'viewport': vp,
                    'group': VARIANTS[vid]['group'], 'variant': vid})
    return out


def post(url, body, headers, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **headers})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            raise RuntimeError(f'{e.code}: {e.read()[:300]!r}')


def b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()


def jev(shot, questions):
    ref = 'shot-' + re.sub(r'[^a-z0-9]', '', shot['id'].lower())[:40]
    body = {'model': 'jev-latest', 'state': {'screenshot': ref},
            'assets': {ref: {'type': 'image', 'format': 'png', 'data_base64': b64(shot['path'])}},
            'questions': {qid: {'type': 'noul', 'instructions': f'About the shop screenshot in `screenshot`: {q}'} for qid, q in questions}}
    t = time.time()
    r = post('https://api.typesafe.ai/v1/systemone', body, {'Authorization': 'Bearer ' + key('jev'), 'TypeSafe-Danger-Zone-Images': 'true'})
    return {'model': r.get('model'), 'answers': {k: v.get('noul') for k, v in r['answers'].items()}, 'usage': r.get('usage'), 'seconds': time.time() - t}


def vlm(model, shot, prompt):
    t = time.time()
    if model.startswith('ollama/'):
        r = post('http://127.0.0.1:11434/api/chat', {'model': model[7:], 'stream': False, 'format': 'json', 'options': {'temperature': 0},
                                                       'messages': [{'role': 'user', 'content': prompt, 'images': [b64(shot['path'])]}]}, {}, timeout=600)
        text, usage = r['message']['content'], {'input_tokens': r.get('prompt_eval_count'), 'output_tokens': r.get('eval_count')}
    else:
        r = post('https://openrouter.ai/api/v1/chat/completions', {
            'model': model, 'temperature': 0, 'response_format': {'type': 'json_object'},
            'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt},
                                                      {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + b64(shot['path'])}}]}]},
            {'Authorization': 'Bearer ' + key('openrouter')})
        text, usage = r['choices'][0]['message']['content'], r.get('usage')
    m = re.search(r'\{.*\}', text or '', re.S)
    try:
        parsed = json.loads(m.group(0)) if m else None
    except ValueError:
        parsed = None
    return {'model': model, 'text': text, 'parsed': parsed, 'usage': usage, 'seconds': time.time() - t}


def pixel(shot, root):
    from PIL import Image, ImageChops
    clean = os.path.join(root, 'clean', f"{shot['screen']}-{shot['viewport']}.png")
    a, b = Image.open(shot['path']).convert('RGB'), Image.open(clean).convert('RGB')
    if a.size != b.size:
        return {'changed': 1.0}
    d = ImageChops.difference(a, b).point(lambda x: 255 if x > 16 else 0).convert('L')
    return {'changed': sum(1 for x in d.getdata() if x) / (a.size[0] * a.size[1])}


def run(root, checker, reps, only):
    out = os.path.join(os.environ.get('VC_RESULTS', os.path.join(E, 'results')), 'raw', checker.replace('/', '_').replace(':', '-'))
    os.makedirs(out, exist_ok=True)
    for shot in shots(root):
        if only and shot['id'] not in only and shot['variant'] not in only and shot['group'] not in only:
            continue
        qs = [(a['id'], a['question']) for a in ASSERT[shot['screen']]]
        for k in range(1 if checker == 'pixel' else reps):
            path = os.path.join(out, f"{shot['id']}.r{k + 1}.json")
            if os.path.exists(path):
                continue
            if checker == 'pixel':
                res = pixel(shot, root)
            elif checker == 'jev-assert':
                res = jev(shot, qs)
            elif checker == 'jev-open':
                res = jev(shot, [('defect', OPEN_Q)])
            elif checker.startswith('vlm-assert:'):
                prompt = ('Look at this screenshot of an online shop and answer each question with "yes" or "no". Answer with '
                          'JSON only, mapping each id to "yes" or "no".\n' + '\n'.join(f'{i}: {q}' for i, q in qs))
                res = vlm(checker.split(':', 1)[1], shot, prompt)
            elif checker.startswith('vlm-review:'):
                res = vlm(checker.split(':', 1)[1], shot, REVIEW)
            else:
                raise SystemExit(f'unknown checker {checker}')
            json.dump({**{k2: shot[k2] for k2 in ('id', 'screen', 'viewport', 'group', 'variant')}, 'rep': k + 1, 'checker': checker, **res},
                      open(path, 'w'), indent=1)
            print(checker, shot['id'], k + 1, flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    reps = int(a[a.index('--reps') + 1]) if '--reps' in a else 3
    only = set(a[a.index('--only') + 1].split(',')) if '--only' in a else set()
    run(a[0], a[1], reps, only)
