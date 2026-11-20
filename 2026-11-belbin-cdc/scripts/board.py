#!/usr/bin/env python3
"""Read-only board: serves the event log and one HTML page. Live and replay use the same page.
usage: board.py [--db path] [--port 8765]"""
import argparse, json, sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
PAGE = (Path(__file__).with_name("board.html")).read_text()


def make_handler(dbpath):
    def q(sql, *a):
        c = sqlite3.connect(f"file:{dbpath}?mode=ro", uri=True)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute(sql, a)]
        finally:
            c.close()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send(self, body, ctype="application/json"):
            b = body if isinstance(body, bytes) else body.encode()
            self.send_response(200); self.send_header("content-type", ctype + "; charset=utf-8"); self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            u = urlparse(self.path); p = parse_qs(u.query)
            if u.path == "/": return self.send(PAGE, "text/html")
            try:
                if u.path == "/api/sessions":
                    return self.send(json.dumps(q("select session, min(ts) start, max(ts) end, sum(kind='message') messages, (select text from events e2 where e2.session=e.session and kind='session_start') models from events e where session<90 group by session order by session")))
                if u.path == "/api/events":
                    s, after = int(p["session"][0]), int(p.get("after", ["0"])[0])
                    return self.send(json.dumps(q("select id,ts,kind,agent,reply_to,seen_upto,head,text,meta from events where session=? and id>? and kind!='usage' order by id", s, after)))
            except (KeyError, ValueError, sqlite3.Error) as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode()); return
            self.send_response(404); self.end_headers()
    return H


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--db", default=str(ROOT / "results" / "events.sqlite")); ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    print(f"board on http://127.0.0.1:{a.port}")
    ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(a.db)).serve_forever()
