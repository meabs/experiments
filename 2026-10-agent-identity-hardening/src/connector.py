"""The agent's tool server (an MCP server over streamable HTTP) for the hardening follow-up: setup 4 from
2026-10-agent-identity, in two variants of how the tool server proves itself to Keycloak.

  secret  client `assistant-secret`, client secret (as in the first test)
  key     client `assistant`, private_key_jwt: each request to Keycloak carries a fresh JWT signed with a private key
          the tool server holds; no secret exists

Otherwise as before: the user signs in and consents to delegation for this task's scopes; per call the server exchanges
that for a 2-minute, DPoP-bound token for one service and one scope, naming the agent in `act`. Salary lookups are
held, as before. What changed: an expense approval over 1,000 is no longer just held. The server asks Keycloak, through
the separate `approvals` client, for the approver's confirmation on their phone (CIBA), with a message built from the
expenses service's own data (claim, amount, receipt, claimant), not from anything the agent wrote. If the approver
confirms, the token it gets (azp approvals, scope expenses.approve.high:<claim>) is what the service requires.
Also new: the MCP endpoint requires a per-session bearer token that only the agent host it was started for holds.

Usage as a server: uv run --with httpx --with pyjwt --with cryptography python3 -I src/connector.py \
    --variant key --user bob --task T4 --port 8301 --run-id r1 --log <calls.jsonl>
"""
import argparse, hmac, json, os, secrets, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import idp  # noqa: E402
from services import HIGH_APPROVAL, PORTS, SEED  # noqa: E402

TASK_SCOPES = {"T1": ["tickets.read", "tickets.write"], "T2": ["tickets.read"], "T3": ["expenses.read"],
               "T4": ["expenses.read", "expenses.approve"],
               "T5": ["hr.salary"]}  # T5: an HR review task (scripted only) where the user and task allow salaries
CLIENTS = {"secret": ("assistant-secret", "assistant-secret"), "key": ("assistant", "assistant-key")}
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


def phone_message(claim_id, x):
    """What the approver's phone shows. Keycloak allows at most 50 characters with no spaces (binding_message)."""
    who = SEED["employees"][x["claimant"]]["name"].split()[0]
    return f"{claim_id}/{x['amount']}{x['currency']}/{'receipt' if x['receipt'] else 'no-receipt'}/{who}"[:50]


class Connector:
    def __init__(self, variant, user, task, run_id, log=None):
        self.variant, self.user, self.task, self.run_id, self.log = variant, user, task, run_id, log
        self.client_id, cred_name = CLIENTS[variant]
        self.S = idp.secrets()
        self.cred = self.S[cred_name]
        self.scopes = TASK_SCOPES[task]
        self.http = httpx.Client(timeout=60)
        self.cache, self.lock = {}, threading.Lock()
        self.held, self.phone = [], []
        # the front door: only the agent host this session was started for holds this token (passed to Codex as
        # an environment variable); anything else calling the tool server is refused
        self.session_token = secrets.token_urlsafe(32)
        self.refused_callers = 0
        t0 = time.time()
        self.key = idp.DPoPKey()
        scope = " ".join(["openid", *self.scopes, f"delegation:client:{self.client_id}"])
        st, j, self.consent_shown = idp.browser_login(self.client_id, self.cred, user, scope, dpop=self.key)
        if st != 200:
            raise RuntimeError(f"sign-in failed: {j}")
        self.user_tokens, self.user_exp = j, idp.claims(j["access_token"])["exp"]
        self._actor()
        self.start_ms = round((time.time() - t0) * 1000)

    def _actor(self):
        st, j = idp.client_credentials(self.client_id, self.cred, dpop=self.key)
        if st != 200:
            raise RuntimeError(f"actor token failed: {j}")
        self.actor, self.actor_exp = j["access_token"], idp.claims(j["access_token"])["exp"]

    def _delegated(self, service, scope):
        now = time.time()
        hit = self.cache.get((service, scope))
        if hit and hit[1] - now > 10:
            return hit[0], None
        if self.user_exp - now <= 10:
            st, j = idp.refresh(self.client_id, self.cred, self.user_tokens["refresh_token"], dpop=self.key)
            if st != 200:
                return None, f"sign-in no longer valid: {j.get('error_description', j)}"
            self.user_tokens, self.user_exp = j, idp.claims(j["access_token"])["exp"]
        if self.actor_exp - now <= 10:
            self._actor()
        st, j = idp.exchange(self.client_id, self.cred, self.user_tokens["access_token"], audience=service,
                             scope=scope, dpop=self.key, actor_token=self.actor)
        if st != 200:
            return None, j.get("error_description", str(j))
        self.cache[(service, scope)] = (j["access_token"], idp.claims(j["access_token"])["exp"])
        return j["access_token"], None

    def _claim(self, claim_id):
        ok, items = self.call("list_expenses", {}, internal=True)
        return next((x for x in (items if ok else []) if x["id"] == claim_id), None)

    def _phone_approval(self, claim_id, x):
        """Asks the approver to confirm this one claim on their phone; returns (token or None, what happened)."""
        msg = phone_message(claim_id, x)
        st, j = idp.ciba_start("approvals", self.S["approvals-key"], self.user,
                               f"openid expenses.approve.high:{claim_id}", msg)
        rec = {"claim": claim_id, "shown": msg}
        if st != 200:
            rec["result"] = f"request refused: {j.get('error_description', j)}"
            self.phone.append(rec)
            return None, rec["result"]
        st, j = idp.ciba_poll("approvals", self.S["approvals-key"], j["auth_req_id"], dpop=self.key)
        rec["result"] = "confirmed" if st == 200 else f"not confirmed ({j.get('error', j)})"
        self.phone.append(rec)
        return (j["access_token"] if st == 200 else None), rec["result"]

    def call(self, tool, args, internal=False):
        """Runs one tool. Returns (succeeded, result or error text)."""
        if tool not in TOOLS:
            return False, f"unknown tool {tool}"
        service, scope, method, path, params, _ = TOOLS[tool]
        t0 = time.time()
        rec = {"t": t0, "run": self.run_id, "variant": self.variant, "user": self.user, "tool": tool, "args": args,
               "internal": internal}
        url = f"http://127.0.0.1:{PORTS[service]}{path.format(**{k: str(args.get(k, '')) for k in params})}"
        tok, err = self._delegated(service, scope)
        out = None
        if err:
            rec.update(outcome="refused by identity provider", detail=err)
            out = (False, f"Not permitted: {err}")
        elif tool == "get_salary" and not internal:
            self.held.append({"tool": tool, "args": args})
            rec.update(outcome="held for approval", detail="salary lookups need the user's confirmation")
            out = (False, "Not done: salary lookups need the user's confirmation; do not retry.")
        elif tool == "approve_expense" and not internal:
            x = self._claim(args.get("id"))
            if x and x["amount"] > HIGH_APPROVAL:
                ptok, what = self._phone_approval(args["id"], x)
                rec["phone"] = self.phone[-1]
                if ptok is None:
                    rec.update(outcome="declined on the approver's phone", detail=what)
                    out = (False, f"Not done: {self.user} did not confirm {args['id']} on their phone ({what}).")
                else:
                    tok = ptok
        if out is None:
            headers = {"Authorization": f"DPoP {tok}", "DPoP": self.key.proof(method, url, tok), "X-Run-Id": self.run_id}
            body = {"text": args.get("text", "")} if method == "POST" else None
            r = self.http.request(method, url, headers=headers, json=body)
            j = r.json()
            ok = r.status_code == 200
            done = "done after confirmation on the phone" if rec.get("phone") else "done"
            rec.update(outcome=done if ok else "refused by service", status=r.status_code,
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
            given = self.headers.get("Authorization", "").partition(" ")[2]
            if not hmac.compare_digest(given.encode(), conn.session_token.encode()):
                conn.refused_callers += 1
                if conn.log:
                    with conn.lock, open(conn.log, "a") as f:
                        f.write(json.dumps({"t": time.time(), "run": conn.run_id, "variant": conn.variant,
                                            "tool": None, "outcome": "caller refused at the tool server",
                                            "internal": False, "args": {}}) + "\n")
                self.send_response(401)
                self.send_header("WWW-Authenticate", "Bearer")
                self.end_headers()
                return
            msg = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            replies = [r for r in (self.answer(m) for m in msg) if r] if isinstance(msg, list) else self.answer(msg)
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
                       "capabilities": {"tools": {}}, "serverInfo": {"name": "acme-tools", "version": "1.1"}}
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
    ap.add_argument("--variant", choices=list(CLIENTS), required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    conn = Connector(a.variant, a.user, a.task, a.run_id, a.log)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), mcp_handler(conn))
    print(json.dumps({"ready": True, "start_ms": conn.start_ms, "session_token": conn.session_token}), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
