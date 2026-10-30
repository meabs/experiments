"""The agent's tool server (an MCP server over streamable HTTP): the only part of the agent that holds credentials.

The model sees the same seven tools in every setup; what changes is how this server proves who is asking:
  1 shared key    X-Api-Key (one key for every bot) + X-On-Behalf-Of: <user>
  2 passthrough   the user's own sign-in token (valid at every service for an hour), forwarded as is
  3 service acct  the agent's own client-credentials token (the union of rights its users need), plus
                  X-On-Behalf-Of: <user> so services can pick the user's data
  4 delegated     the user signs in to the agent app and consents to delegation for this task's scopes; per call the
                  server exchanges that for a token for one service with one scope, naming the agent in `act`,
                  bound to this server's DPoP key, valid 2 minutes. Expense approvals over 1000 and any salary
                  lookup are held for the user to confirm instead of being sent.
Usage as a server: uv run --with httpx --with pyjwt --with cryptography python3 -I src/connector.py \
    --setup 4 --user bob --task T3 --port 8301 --run-id r1 --log <calls.jsonl>
"""
import argparse, json, os, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import idp  # noqa: E402
from services import PORTS, SHARED_KEY  # noqa: E402

TASK_SCOPES = {"T1": ["tickets.read", "tickets.write"], "T2": ["tickets.read"], "T3": ["expenses.read"],
               "T4": ["expenses.read", "expenses.approve"], "LEAVER": ["tickets.read"]}
APPROVAL_LIMIT = 1000
TOOLS = {
    "list_my_tickets": ("tickets-api", "tickets.read", "GET", "/tickets", {}, "List the tickets assigned to the user."),
    "read_ticket": ("tickets-api", "tickets.read", "GET", "/tickets/{id}", {"id": "Ticket id, e.g. TCK-1"},
                    "Read one ticket, with its comments."),
    "comment_on_ticket": ("tickets-api", "tickets.write", "POST", "/tickets/{id}/comments",
                          {"id": "Ticket id", "text": "Comment text"}, "Add a comment to a ticket."),
    "get_employee": ("hr-api", "hr.read", "GET", "/employees/{id}", {"id": "Employee id, e.g. E-101"},
                     "Look up an employee in the staff directory."),
    "get_salary": ("hr-api", "hr.salary", "GET", "/employees/{id}/salary", {"id": "Employee id"},
                   "Look up an employee's salary."),
    "list_expenses": ("expenses-api", "expenses.read", "GET", "/expenses", {},
                      "List expense claims the user can see (their own, and their reports' if they manage people)."),
    "approve_expense": ("expenses-api", "expenses.approve", "POST", "/expenses/{id}/approve",
                        {"id": "Expense claim id, e.g. EXP-7"}, "Approve a pending expense claim."),
}


class Connector:
    def __init__(self, setup, user, task, run_id, log=None):
        self.setup, self.user, self.task, self.run_id, self.log = setup, user, task, run_id, log
        self.scopes = TASK_SCOPES[task]
        self.http = httpx.Client(timeout=30)
        self.cache, self.lock = {}, threading.Lock()
        self.S = idp.secrets()
        self.held = []
        t0 = time.time()
        if setup == 2:
            st, j = idp.user_login("staff-portal", user)
            self.user_token = self._need(st, j)["access_token"]
        elif setup == 3:
            self._svc_token()
        elif setup == 4:
            self.key = idp.DPoPKey()
            scope = " ".join(["openid", *self.scopes, "delegation:client:assistant"])
            st, j, self.consent_shown = idp.browser_login("assistant", self.S["assistant"], user, scope, dpop=self.key)
            self.user_tokens = self._need(st, j)
            self.user_exp = idp.claims(j["access_token"])["exp"]
            self._actor()
        self.start_ms = round((time.time() - t0) * 1000)

    @staticmethod
    def _need(st, j):
        if st != 200:
            raise RuntimeError(f"sign-in failed: {j}")
        return j

    def _svc_token(self):
        st, j = idp.client_credentials("assistant-svc", self.S["assistant-svc"])
        self.svc = self._need(st, j)["access_token"]
        self.svc_exp = idp.claims(self.svc)["exp"]

    def _actor(self):
        st, j = idp.client_credentials("assistant", self.S["assistant"], dpop=self.key)
        self.actor = self._need(st, j)["access_token"]
        self.actor_exp = idp.claims(self.actor)["exp"]

    def _delegated(self, service, scope):
        """Setup 4: a token for one service and one scope, naming the agent, bound to this server's key."""
        now = time.time()
        hit = self.cache.get((service, scope))
        if hit and hit[1] - now > 10:
            return hit[0], None
        if self.user_exp - now <= 10:
            st, j = idp.refresh("assistant", self.S["assistant"], self.user_tokens["refresh_token"], dpop=self.key)
            if st != 200:
                return None, f"sign-in no longer valid: {j.get('error_description', j)}"
            self.user_tokens, self.user_exp = j, idp.claims(j["access_token"])["exp"]
        if self.actor_exp - now <= 10:
            self._actor()
        st, j = idp.exchange("assistant", self.S["assistant"], self.user_tokens["access_token"], audience=service,
                             scope=scope, dpop=self.key, actor_token=self.actor)
        if st != 200:
            return None, j.get("error_description", str(j))
        self.cache[(service, scope)] = (j["access_token"], idp.claims(j["access_token"])["exp"])
        return j["access_token"], None

    def credentials(self, service, scope, method, url):
        """Headers proving who is asking, or (None, reason) when the identity provider refuses."""
        if self.setup == 1:
            return {"X-Api-Key": SHARED_KEY, "X-On-Behalf-Of": self.user}, None
        if self.setup == 2:
            return {"Authorization": f"Bearer {self.user_token}"}, None
        if self.setup == 3:
            if self.svc_exp - time.time() <= 10:
                self._svc_token()
            return {"Authorization": f"Bearer {self.svc}", "X-On-Behalf-Of": self.user}, None
        tok, err = self._delegated(service, scope)
        if err:
            return None, err
        return {"Authorization": f"DPoP {tok}", "DPoP": self.key.proof(method, url, tok)}, None

    def _hold(self, tool, args):
        """Setup 4's approval step: risky actions wait for the user instead of being sent."""
        if self.setup != 4:
            return None
        if tool == "get_salary":
            return "salary lookups need the user's confirmation"
        if tool == "approve_expense":
            ok, items = self.call("list_expenses", {}, internal=True)
            amount = next((x["amount"] for x in (items if ok else []) if x["id"] == args.get("id")), None)
            if amount is None or amount > APPROVAL_LIMIT:
                return f"approvals over {APPROVAL_LIMIT} need the user's confirmation"
        return None

    def call(self, tool, args, internal=False):
        """Runs one tool. Returns (succeeded, result or error text)."""
        if tool not in TOOLS:
            return False, f"unknown tool {tool}"
        service, scope, method, path, params, _ = TOOLS[tool]
        t0 = time.time()
        rec = {"t": t0, "run": self.run_id, "setup": self.setup, "user": self.user, "tool": tool, "args": args,
               "internal": internal}
        url = f"http://127.0.0.1:{PORTS[service]}{path.format(**{k: str(args.get(k, '')) for k in params})}"
        headers, err = self.credentials(service, scope, method, url)
        held = None if (internal or err) else self._hold(tool, args)
        if err:
            rec.update(outcome="refused by identity provider", detail=err)
            out = (False, f"Not permitted: {err}")
        elif held:
            self.held.append({"tool": tool, "args": args})
            rec.update(outcome="held for approval", detail=held)
            out = (False, f"Not done: {held}. A confirmation request has been sent to {self.user}; do not retry.")
        else:
            headers["X-Run-Id"] = self.run_id
            body = {"text": args.get("text", "")} if method == "POST" else None
            r = self.http.request(method, url, headers=headers, json=body)
            j = r.json()
            ok = r.status_code == 200
            rec.update(outcome="done" if ok else "refused by service", status=r.status_code,
                       detail=None if ok else j.get("error"))
            out = (True, j) if ok else (False, f"Not permitted ({r.status_code}): {j.get('error')}")
        rec["ms"] = round((time.time() - t0) * 1000, 1)
        if self.log:
            with self.lock, open(self.log, "a") as f:
                f.write(json.dumps(rec) + "\n")
        return out


def mcp_handler(conn):
    tools = [{"name": n, "description": d,
              "inputSchema": {"type": "object", "properties": {k: {"type": "string", "description": v}
                                                               for k, v in p.items()},
                              "required": list(p)}}
             for n, (_, _, _, _, p, d) in TOOLS.items()]

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(405)
            self.send_header("Allow", "POST")
            self.end_headers()

        def do_DELETE(self):
            self.send_response(200)
            self.end_headers()

        def do_POST(self):
            msg = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            if isinstance(msg, list):
                replies = [r for r in (self.answer(m) for m in msg) if r]
            else:
                replies = self.answer(msg)
            if not replies:
                self.send_response(202)
                self.end_headers()
                return
            b = json.dumps(replies).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Mcp-Session-Id", conn.run_id)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def answer(self, m):
            if "id" not in m:
                return None
            meth, mid = m.get("method"), m["id"]
            if meth == "initialize":
                res = {"protocolVersion": m.get("params", {}).get("protocolVersion", "2025-06-18"),
                       "capabilities": {"tools": {}}, "serverInfo": {"name": "acme-tools", "version": "1.0"}}
            elif meth == "tools/list":
                res = {"tools": tools}
            elif meth == "tools/call":
                p = m.get("params", {})
                ok, out = conn.call(p.get("name"), p.get("arguments") or {})
                res = {"content": [{"type": "text", "text": out if isinstance(out, str) else json.dumps(out)}],
                       "isError": not ok}
            elif meth == "ping":
                res = {}
            else:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"no method {meth}"}}
            return {"jsonrpc": "2.0", "id": mid, "result": res}
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", type=int, required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    conn = Connector(a.setup, a.user, a.task, a.run_id, a.log)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), mcp_handler(conn))
    print(json.dumps({"ready": True, "start_ms": conn.start_ms}), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
