#!/usr/bin/env python3
"""Loopback-only graphical observer. No arbitrary file or model access."""
import argparse
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import time

ROOT = Path(__file__).resolve().parents[1]


def load_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def view():
    lifecycle = load_json(ROOT / "results" / "status.json", {})
    folder = ROOT / "results" / "main"
    if lifecycle.get("phase") == "pilot":
        folder = ROOT / "results" / "pilot"
    db = sqlite3.connect(f"file:{folder / 'world.sqlite3'}?mode=ro", uri=True, timeout=10)
    db.execute("BEGIN")
    row = db.execute("SELECT value FROM meta WHERE key='world'").fetchone()
    world = json.loads(row[0])
    events = [dict(id=i, step=step, **json.loads(payload)) for i, step, payload in db.execute(
        "SELECT id,step,payload FROM events ORDER BY id DESC LIMIT 180")]
    counts = {t: Counter() for t in world["towns"]}
    for t, kind, n in db.execute("SELECT json_extract(payload,'$.town'), json_extract(payload,'$.kind'), COUNT(*) FROM events GROUP BY 1,2"):
        counts[t][kind] = n
    token_row = db.execute("SELECT COUNT(*),COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0),COALESCE(AVG(seconds),0),COALESCE(SUM(accepted),0) FROM decisions").fetchone()
    snapshots = []
    for day, payload in db.execute("SELECT day,payload FROM snapshots ORDER BY day DESC LIMIT 80"):
        past = json.loads(payload)
        snapshots.append(dict(day=day, towns={t: dict(food=sum(a["inventory"]["food"] for a in v["agents"].values()),
                              alive=sum(a["health"] > 0 for a in v["agents"].values()),
                              homes=sum(a["home"] for a in v["agents"].values()),
                              projects=sum(p["level"] for p in v["projects"].values())) for t, v in past["towns"].items()}))
    db.close()
    return dict(world=world, events=events, counts=counts, snapshots=snapshots[::-1],
                lifecycle=lifecycle, runtime=load_json(folder / "status.json", {}),
                verification=load_json(folder / "verification.json", {}),
                totals=dict(calls=token_row[0], input_tokens=token_row[1], output_tokens=token_row[2],
                            mean_seconds=token_row[3], accepted=token_row[4]),
                pilot=folder.name == "pilot", now=time.time(),
                paused=(ROOT / "results" / "main" / "PAUSE").exists())


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body, mime="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def allowed_host(self):
        return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

    def do_GET(self):
        if not self.allowed_host():
            return self.reply(403, {"error": "loopback host required"})
        path = self.path.split("?", 1)[0]
        if path == "/api/state":
            try:
                return self.reply(200, view())
            except Exception as error:
                return self.reply(503, {"error": str(error)})
        files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "application/javascript"), "/style.css": ("style.css", "text/css")}
        if path not in files:
            return self.reply(404, {"error": "not found"})
        name, mime = files[path]
        return self.reply(200, (ROOT / "web" / name).read_bytes(), mime)

    def do_POST(self):
        origin = self.headers.get("Origin")
        if not self.allowed_host() or origin != f"http://{self.headers.get('Host')}" or self.headers.get("Content-Type") != "application/json":
            return self.reply(403, {"error": "same-origin JSON required"})
        if int(self.headers.get("Content-Length", "0")) > 128:
            return self.reply(413, {"error": "body too large"})
        folder = ROOT / "results" / "main"
        if self.path == "/api/pause":
            (folder / "PAUSE").touch()
        elif self.path == "/api/resume":
            (folder / "PAUSE").unlink(missing_ok=True)
        elif self.path == "/api/stop":
            (folder / "STOP").touch()
            (ROOT / "results" / "STOP").touch()
        else:
            return self.reply(404, {"error": "unknown control"})
        return self.reply(200, {"ok": True, "note": "Takes effect between model calls; an in-flight call may take up to 180 seconds."})

    def log_message(self, fmt, *args):
        if args and str(args[1] if len(args) > 1 else "").startswith("5"):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Agent Society: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
