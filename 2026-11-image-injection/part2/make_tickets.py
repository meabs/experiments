"""Part 2 set-up: the workspace every run starts from, each ticket's screenshot, and its injected copies.

  python3 -I make_tickets.py base                 storefront source (okf-local's 455b4bc, no node_modules) -> $II_WORK/base
  python3 -I make_tickets.py shots                ticket screenshots (needs visual-checks' serve.py started with
                                                  VC_VARIANTS=part2/tickets.json VC_STATE=$II_WORK/state) -> images/<ticket>/clean.png
  python3 -I make_tickets.py inject               every technique x framing, and the checker-aware copies (fixed seed)
  python3 -I make_tickets.py check                each hidden test fails on its planted workspace (needs base)

$II_WORK defaults to ~/code/benchmark/ii-work. The planted bug is part of the workspace's one commit, so git history
doesn't give it away.
"""
import json, os, random, shutil, subprocess, sys, tempfile

P2 = os.path.dirname(os.path.abspath(__file__))
E = os.path.dirname(P2)
sys.path.insert(0, os.path.join(E, 'scripts'))
sys.path.insert(0, os.path.join(E, '..', '2026-11-visual-checks', 'scripts'))
WORK = os.environ.get('II_WORK', os.path.expanduser('~/code/benchmark/ii-work'))
APP = os.path.expanduser('~/code/benchmark/vc-work/app')
TICKETS = json.load(open(os.path.join(P2, 'tickets.json')))
HARNESS = os.path.join(E, '..', '2026-10-okf-local', 'harness', 'register.mjs')


def base():
    d = os.path.join(WORK, 'base')
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    tar = subprocess.run(['git', '-C', APP, 'archive', 'HEAD'], capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', d], input=tar, check=True)
    print(d, sum(len(f) for _, _, f in os.walk(d)), 'files')


def workspace(ticket, dest):
    """A fresh git repository: the storefront with this ticket's bug planted, in one commit."""
    shutil.copytree(os.path.join(WORK, 'base'), dest)
    pl = ticket['plant']
    if pl:
        p = os.path.join(dest, pl['file']); s = open(p).read()
        assert s.count(pl['old']) == 1, (ticket['id'], 'plant target not found once')
        open(p, 'w').write(s.replace(pl['old'], pl['new']))
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'shop', 'GIT_AUTHOR_EMAIL': 'shop@example.invalid', 'GIT_COMMITTER_NAME': 'shop',
           'GIT_COMMITTER_EMAIL': 'shop@example.invalid', 'GIT_AUTHOR_DATE': '2026-10-01T09:00:00', 'GIT_COMMITTER_DATE': '2026-10-01T09:00:00'}
    for cmd in (['init', '-q', '-b', 'main'], ['add', '-A'], ['commit', '-q', '-m', 'storefront']):
        subprocess.run(['git', '-C', dest] + cmd, check=True, env=env)


def hidden_test(ticket, ws):
    r = subprocess.run(['node', '--experimental-default-type=module', '--import', HARNESS,
                        os.path.join(P2, 'hidden', ticket['id'] + '.test.mjs')], cwd=ws, capture_output=True, text=True, timeout=120)
    return r.returncode == 0, (r.stdout + r.stderr)[-600:]


def shots():
    from shoot import shoot
    state = os.path.join(WORK, 'state')
    try:
        for t in TICKETS:
            open(state, 'w').write(t['id'])
            d = os.path.join(P2, 'images', t['id']); os.makedirs(d, exist_ok=True)
            p = shoot(d, t['screen'], 'desktop')
            os.replace(p, os.path.join(d, 'clean.png')); print(t['id'])
    finally:
        open(state, 'w').write('')


def inject():
    from PIL import Image
    from conditions import CHECKER_AWARE, FRAMINGS, HARD_TECHNIQUES, TECHNIQUES, TRANSLATED
    from make_images import plant
    rng = random.Random(2)
    for t in TICKETS:
        d = os.path.join(P2, 'images', t['id'])
        im = Image.open(os.path.join(d, 'clean.png'))
        for tech in TECHNIQUES + HARD_TECHNIQUES:
            for fr in FRAMINGS:
                text = TRANSLATED[fr] if tech == 'translated' else FRAMINGS[fr]
                plant(im, tech, text, rng).save(os.path.join(d, f'{tech}__{fr}.png'))
                plant(im, tech, text + ' ' + CHECKER_AWARE, rng).save(os.path.join(d, f'{tech}__{fr}__aware.png'))
        print(t['id'], len(os.listdir(d)))


def check():
    for t in TICKETS:
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, 'ws'); workspace(t, ws)
            ok, out = hidden_test(t, ws)
            print(t['id'], 'FAILS on the planted workspace (as it should)' if not ok else 'PASSES: BAD', out.strip().splitlines()[-1:])


if __name__ == '__main__':
    {'base': base, 'shots': shots, 'inject': inject, 'check': check}[sys.argv[1]]()
