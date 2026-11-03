"""Screenshots of the storefront's five screens at desktop and mobile size, offline (every host except this machine is
blocked, so the page's Google Maps and Stripe scripts never load). Needs app/mock-api/serve.py running.

  python3 -I shoot.py <out dir> [screen ...]       clean screens: <screen>-<viewport>.png
  python3 -I shoot.py --variants <out dir>         every variant in variants/variants.json: <variant>/<screen>-<viewport>.png
"""
import os, subprocess, sys

PAGES = {'home': '/', 'category': '/category/1', 'product': '/product/1', 'cart': '/cart', 'checkout': '/checkout'}
VIEWPORTS = {'desktop': '1280,1500', 'mobile': '390,844'}
BLOCK = '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost'


def shoot(out, page, vp):
    path = os.path.join(out, f'{page}-{vp}.png')
    args = ['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', BLOCK,
            f'--window-size={VIEWPORTS[vp]}', '--virtual-time-budget=10000', f'--screenshot={path}',
            f'http://127.0.0.1:3000{PAGES[page]}']
    if vp == 'mobile':
        args.insert(-1, '--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148')
    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90, check=True)
    return path


STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'mock-api', 'current-variant')


def variants(out):
    import json
    vs = json.load(open(os.path.join(os.path.dirname(STATE), '..', '..', 'variants', 'variants.json')))
    try:
        for v in vs:
            open(STATE, 'w').write(v['id'])
            d = os.path.join(out, v['id'])
            os.makedirs(d, exist_ok=True)
            for page in v['screens']:
                for vp in v['viewports']:
                    print(shoot(d, page, vp))
    finally:
        open(STATE, 'w').write('')


if __name__ == '__main__':
    if sys.argv[1] == '--variants':
        variants(sys.argv[2])
        sys.exit()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for page in sys.argv[2:] or PAGES:
        for vp in VIEWPORTS:
            print(shoot(out, page, vp))
