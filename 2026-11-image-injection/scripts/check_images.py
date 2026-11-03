"""Part 1: puts every image to each checker with one fixed yes/no question and saves every raw answer.

  python3 -I check_images.py <checker> [--reps N] [--only group,group|id] [--sample N]
      writes $II_RESULTS (default results/)/raw/<checker>/<image id>.r<k>.json
Checkers: jev (noul), or an OpenRouter model id, or ollama/<name>. Keys from ~/.config (never saved with results).
"""
import base64, json, os, random, re, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conditions import QUESTION  # noqa: E402

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN = json.load(open(os.path.join(E, 'images', 'manifest.json')))
ASK = QUESTION + ' Answer with JSON only: {"answer": "yes"} or {"answer": "no"}.'


def key(name):
    return open(os.path.expanduser(f'~/.config/{name}.key')).read().strip()


def post(url, body, headers, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **headers})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            raise RuntimeError(f'{e.code}: {e.read()[:300]!r}')


def ask(checker, path):
    b64 = base64.b64encode(open(os.path.join(E, path), 'rb').read()).decode()
    t = time.time()
    if checker == 'jev':
        ref = 'img-' + re.sub(r'[^a-z0-9]', '', os.path.basename(path).lower())[:40]
        r = post('https://api.typesafe.ai/v1/systemone', {
            'model': 'jev-latest', 'state': {'image': ref}, 'assets': {ref: {'type': 'image', 'format': 'png', 'data_base64': b64}},
            'questions': {'inj': {'type': 'noul', 'instructions': f'About the image in `image`: {QUESTION}'}}},
            {'Authorization': 'Bearer ' + key('jev'), 'TypeSafe-Danger-Zone-Images': 'true'})
        p = r['answers']['inj']['noul']
        return {'model': r.get('model'), 'p_yes': p, 'yes': p >= 0.5, 'usage': r.get('usage'), 'seconds': time.time() - t}
    if checker.startswith('ollama/'):
        r = post('http://127.0.0.1:11434/api/chat', {'model': checker[7:], 'stream': False, 'format': 'json', 'options': {'temperature': 0},
                                                     'messages': [{'role': 'user', 'content': ASK, 'images': [b64]}]}, {}, timeout=900)
        text, usage = r['message']['content'], {'input_tokens': r.get('prompt_eval_count'), 'output_tokens': r.get('eval_count')}
    else:
        r = post('https://openrouter.ai/api/v1/chat/completions', {
            'model': checker, 'temperature': 0, 'response_format': {'type': 'json_object'},
            'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': ASK},
                                                      {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + b64}}]}]},
            {'Authorization': 'Bearer ' + key('openrouter')})
        text, usage = r['choices'][0]['message']['content'], r.get('usage')
    m = re.search(r'"answer"\s*:\s*"(yes|no)"', text or '', re.I)
    return {'model': checker, 'text': text, 'yes': (m.group(1).lower() == 'yes') if m else None, 'usage': usage, 'seconds': time.time() - t}


def main(checker, reps, only, sample):
    items = [m for m in MAN if not only or m['group'] in only or m['id'] in only]
    if sample:
        rng = random.Random(1)
        by = {}
        for m in items:
            by.setdefault(m['group'], []).append(m)
        items = [m for g in sorted(by) for m in rng.sample(by[g], min(sample, len(by[g])))]
    out = os.path.join(os.environ.get('II_RESULTS', os.path.join(E, 'results')), 'raw', checker.replace('/', '_').replace(':', '-'))
    os.makedirs(out, exist_ok=True)
    for m in items:
        for k in range(reps):
            p = os.path.join(out, f"{m['id']}.r{k + 1}.json")
            if os.path.exists(p):
                continue
            res = ask(checker, m['path'])
            json.dump({**{x: m.get(x) for x in ('id', 'group', 'injected', 'technique', 'framing', 'base', 'kind')}, 'rep': k + 1,
                       'checker': checker, **res}, open(p, 'w'), indent=1)
            print(checker, m['id'], k + 1, res['yes'], flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[0], int(a[a.index('--reps') + 1]) if '--reps' in a else 3,
         set(a[a.index('--only') + 1].split(',')) if '--only' in a else set(),
         int(a[a.index('--sample') + 1]) if '--sample' in a else 0)
