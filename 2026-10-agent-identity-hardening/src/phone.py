"""A stand-in for each person's phone, as Keycloak's CIBA "authentication channel": Keycloak tells it a client wants the
user to confirm something; the phone shows the message and the person answers.

Usage: uv run --with httpx python3 -I src/phone.py <log.jsonl>          (listens on 127.0.0.1:8400)
POST /notify      called by Keycloak: JSON with login_hint, binding_message, scope; Authorization: Bearer <ticket>
POST /policy      {"mode": "receipt" | "approve" | "decline"} sets how the scripted person answers
The scripted person (design, "The person on the phone"): in mode "receipt" they approve only if the message they are
shown says the claim has a receipt; "approve" and "decline" answer everything the same way. They answer after 1 s by
calling Keycloak's callback with the ticket. Every notification and answer is logged.
"""
import json, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

CALLBACK = "http://127.0.0.1:8180/realms/acme/protocol/openid-connect/ext/ciba/auth/callback"
LOG = None
mode = {"value": "receipt"}
lock = threading.Lock()


def decide(message):
    if mode["value"] == "approve":
        return True
    if mode["value"] == "decline":
        return False
    m = message.lower()
    return "receipt" in m and "no-receipt" not in m and "noreceipt" not in m


def answer(ticket, entry):
    time.sleep(1)
    status = "SUCCEED" if entry["approved"] else "UNAUTHORIZED"
    r = httpx.post(CALLBACK, json={"status": status}, headers={"Authorization": f"Bearer {ticket}"}, timeout=30)
    entry.update(callback_status=r.status_code, answered=status)
    with lock, open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if self.path == "/policy":
            mode["value"] = body["mode"]
            self.send_response(200)
            self.end_headers()
            return
        ticket = self.headers.get("Authorization", "").partition(" ")[2]
        entry = {"t": time.time(), "user": body.get("login_hint"), "shown": body.get("binding_message"),
                 "scope": body.get("scope"), "mode": mode["value"]}
        entry["approved"] = decide(entry["shown"] or "")
        threading.Thread(target=answer, args=(ticket, entry), daemon=True).start()
        self.send_response(201)
        self.end_headers()


if __name__ == "__main__":
    LOG = sys.argv[1]
    print("phone up on 8400", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8400), H).serve_forever()
