"""Serves the built storefront (port 3000, unknown paths fall back to index.html) and a mock Shopizer API (port 8099)
answering from fixtures.json, so every screenshot is reproducible. Unknown API paths are logged and get an empty answer.

  python3 -I serve.py <build dir> [log file]
"""
import io, json, os, re, sys, threading
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.abspath(sys.argv[1])
LOG = open(sys.argv[2] if len(sys.argv) > 2 else os.devnull, 'a')


SEED = ('<script>if(!localStorage.getItem("redux_localstorage_simple"))localStorage.setItem("redux_localstorage_simple",'
        'JSON.stringify({'
        'productData:{products:[],productid:1,categoryid:""},'
        'cartData:{cartItems:{},cartID:"VC-CART-1",cartCount:0,orderID:""}}));</script>')


def fixtures():
    p = os.path.join(HERE, 'fixtures.json')
    return json.load(open(p)) if os.path.exists(p) else []


class App(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=BUILD, **k)

    def translate_path(self, path):
        if path.startswith('/mock-img/'):  # product pictures for the fixtures
            return os.path.join(HERE, 'img', os.path.basename(path.split('?')[0]))
        return super().translate_path(path)

    def send_head(self):
        path = self.translate_path(self.path.split('?')[0])
        if not os.path.exists(path) or self.path.split('?')[0] in ('/', '/index.html'):
            # the page: index.html with the state seed first, so a fresh browser opens with product 1 and the fixture
            # cart selected (the storefront keeps both in saved app state, normally set by clicking through)
            html = open(os.path.join(BUILD, 'index.html'), encoding='utf-8').read().replace('<head>', '<head>' + SEED, 1)
            data = html.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            return io.BytesIO(data)
        return super().send_head()

    def end_headers(self):
        # every visit starts with the same cart (the storefront reads its id from this cookie)
        self.send_header('Set-Cookie', 'DEFAULT_shopizer_cart=VC-CART-1; Path=/')
        self.send_header('Set-Cookie', 'CookieConsent=true; Path=/')
        super().end_headers()

    def log_message(self, *a):
        pass


class Api(BaseHTTPRequestHandler):
    def _answer(self):
        path = self.path.split('/api/v1/', 1)[-1]
        body, status, hit = '{}', 200, None
        for f in fixtures():  # first match wins: {"method": "GET", "path": "regex", "body": ...}
            if f.get('method', 'GET') == self.command and re.fullmatch(f['path'], path):
                body, status, hit = json.dumps(f['body']), f.get('status', 200), f['path']
                break
        LOG.write(f'{self.command} {path} -> {hit or "EMPTY"}\n'); LOG.flush()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.end_headers()
        self.wfile.write(body.encode())

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _answer

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in [('Access-Control-Allow-Origin', '*'), ('Access-Control-Allow-Headers', '*'), ('Access-Control-Allow-Methods', '*')]:
            self.send_header(k, v)
        self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    api = ThreadingHTTPServer(('127.0.0.1', 8099), Api)
    threading.Thread(target=api.serve_forever, daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1', 3000), App).serve_forever()
