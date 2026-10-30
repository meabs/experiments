"""Scripted scenarios for the hardening follow-up (no model involved).

Usage: uv run --with httpx --with pyjwt --with cryptography python3 -I src/scenarios.py <out dir> [names...]
Names: stolen approvals boundaries regression (default: all). Needs Keycloak (realm.py, with the CIBA channel pointed at the
phone), services.py and phone.py running. Writes <out>/<name>.json and prints each.

stolen      Item 1. For each variant (client secret; private_key_jwt), an attacker copies what the tool server holds
            apart from any private key: the user's sign-in tokens (access and refresh), a per-service token, and the
            client credential as it would appear in config or a request log (the secret; or a client assertion the
            tool server has already used). Can they refresh the sign-in onto their own key, and then approve?
approvals   Item 2. The service-enforced approval: can a normal approve token, a token for another claim, or the
            assistant's own client get past it; what does the approver see; what if the attacker also holds the
            approvals client's key (whole-host compromise), with a careful and a careless approver.
boundaries  The reviewer's points: B, the services check the agent's own permitted capabilities even when the user and
            the task allow the action; C, a 900 claim with a false pre-approval and no receipt (under the confirmation
            limit); E, another process calling the tool server without its session token.
regression  Ordinary work in the private-key variant: the setup-4 results from the first test still hold.
"""
import json, os, sys, time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import idp  # noqa: E402
from connector import Connector, phone_message  # noqa: E402
from services import PORTS, SEED  # noqa: E402

EXP = f"http://127.0.0.1:{PORTS['expenses-api']}/expenses"


def reset(mode="receipt"):
    httpx.post("http://127.0.0.1:8201/reset").raise_for_status()
    httpx.post("http://127.0.0.1:8400/policy", json={"mode": mode}).raise_for_status()


def res(st_j):
    st, j = st_j
    return {"allowed": st == 200, "status": st, "error": None if st == 200 else j.get("error_description", j.get("error"))}


def call(tok, key, method, url):
    """Uses a DPoP-bound token with a given key."""
    r = httpx.request(method, url, headers={"Authorization": f"DPoP {tok}", "DPoP": key.proof(method, url, tok)},
                      timeout=30)
    return {"allowed": r.status_code == 200, "status": r.status_code,
            "error": None if r.status_code == 200 else r.json().get("error")}


def takeover(client_id, cred, refreshed, attacker):
    """With a refreshed sign-in bound to the attacker's key: exchange for approve rights and try two approvals."""
    actor = idp.client_credentials(client_id, cred, dpop=attacker)[1].get("access_token")
    st, j = idp.exchange(client_id, cred, refreshed["access_token"], audience="expenses-api",
                         scope="expenses.approve", dpop=attacker, actor_token=actor)
    out = {"exchange for approve rights": res((st, j))}
    if st == 200:
        out["approve EXP-7 (84)"] = call(j["access_token"], attacker, "POST", f"{EXP}/EXP-7/approve")
        out["approve EXP-9 (4,800)"] = call(j["access_token"], attacker, "POST", f"{EXP}/EXP-9/approve")
    return out


def stolen():
    out = {}
    for variant in ("secret", "key"):
        reset()
        c = Connector(variant, "bob", "T4", f"stolen-{variant}")
        c.call("list_expenses", {})
        rt = c.user_tokens["refresh_token"]
        attacker = idp.DPoPKey()
        r = {"what was copied": "the sign-in tokens, a per-service token and the client "
                                + ("secret" if variant == "secret" else "assertion from a request log (already used); "
                                   "not the private key")}
        if variant == "secret":
            copied = c.cred
        else:
            a = idp.assertion(c.client_id, c.cred)
            # the tool server uses it (it appears in a log), then the attacker replays it
            r["the tool server's own use of that assertion"] = res(idp.client_credentials(
                c.client_id, {"assertion": a}, dpop=c.key))
            copied = {"assertion": a}
        r["refresh with no client authentication"] = res(idp.refresh(c.client_id, None, rt, dpop=attacker))
        st, j = idp.refresh(c.client_id, copied, rt, dpop=attacker)
        r["refresh with the copied " + ("secret" if variant == "secret" else "assertion, at once")] = res((st, j))
        if variant == "key":
            fake = {"pem": attacker_pem(), "kid": c.cred["kid"]}
            r["refresh with an assertion signed by the attacker's own key"] = res(
                idp.refresh(c.client_id, fake, rt, dpop=attacker))
        if st == 200:
            r["after refreshing"] = takeover(c.client_id, copied if variant == "secret" else c.cred, j, attacker)
        # a host compromise: the attacker also has the tool server's DPoP key, so the per-service token works,
        # but only for what it was issued for
        tok = c.cache[("expenses-api", "expenses.read")][0]
        st2, j2 = idp.exchange(c.client_id, c.cred, c.user_tokens["access_token"], audience="expenses-api",
                               scope="expenses.approve", dpop=c.key, actor_token=c.actor)
        r["with the tool server's own keys too: approve EXP-9 (4,800) with a normal approve token"] = (
            call(j2["access_token"], c.key, "POST", f"{EXP}/EXP-9/approve") if st2 == 200 else res((st2, j2)))
        out[variant] = r
    # the assertion again after it has expired (60 s)
    reset()
    c = Connector("key", "bob", "T4", "stolen-key-late")
    a = idp.assertion(c.client_id, c.cred)
    time.sleep(65)
    out["key"]["refresh with a captured assertion after it expired (65 s)"] = res(
        idp.refresh(c.client_id, {"assertion": a}, c.user_tokens["refresh_token"], dpop=idp.DPoPKey()))
    return out


def attacker_pem():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    return ec.generate_private_key(ec.SECP256R1()).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()


def approvals():
    S = idp.secrets()
    out = {}
    reset("receipt")
    c = Connector("key", "bob", "T4", "approvals")
    out["what the approver's phone shows (EXP-9)"] = phone_message("EXP-9", SEED["expenses"]["EXP-9"])
    out["what the approver's phone shows (EXP-10)"] = phone_message("EXP-10", SEED["expenses"]["EXP-10"])
    out["a readable message with spaces"] = res(idp.ciba_start(
        "approvals", S["approvals-key"], "bob", "openid expenses.approve.high:EXP-9",
        "Approve EXP-9: 4,800 GBP, no receipt, Northwind Advisory"))
    # a normal approve token (the agent's, with its key) on a large claim
    st, j = idp.exchange(c.client_id, c.cred, c.user_tokens["access_token"], audience="expenses-api",
                         scope="expenses.approve", dpop=c.key, actor_token=c.actor)
    out["normal approve token on EXP-9 (4,800)"] = call(j["access_token"], c.key, "POST", f"{EXP}/EXP-9/approve")
    # the assistants cannot get the approval scope themselves
    for cid, cred in (("assistant", S["assistant-key"]), ("assistant-secret", S["assistant-secret"])):
        k = idp.DPoPKey()
        actor = idp.client_credentials(cid, cred, dpop=k)[1].get("access_token")
        st_u, u, _ = idp.browser_login(cid, cred, "bob", f"openid expenses.read expenses.approve delegation:client:{cid}",
                                       dpop=k)
        out[f"{cid}: exchange for expenses.approve.high:EXP-9"] = res(idp.exchange(
            cid, cred, u["access_token"], audience="expenses-api", scope="expenses.approve.high:EXP-9", dpop=k,
            actor_token=actor))
        out[f"{cid}: start a phone approval itself"] = res(idp.ciba_start(
            cid, cred, "bob", "openid expenses.approve.high:EXP-9", "EXP-9/4800GBP/no-receipt/Dave"))
    # a confirmed token for EXP-10 used on EXP-9, then on EXP-10
    k = idp.DPoPKey()
    st, j = idp.ciba_start("approvals", S["approvals-key"], "bob", "openid expenses.approve.high:EXP-10",
                           phone_message("EXP-10", SEED["expenses"]["EXP-10"]))
    st, t = idp.ciba_poll("approvals", S["approvals-key"], j["auth_req_id"], dpop=k)
    out["EXP-10 confirmed on the phone"] = res((st, t))
    if st == 200:
        out["EXP-10's token used on EXP-9"] = call(t["access_token"], k, "POST", f"{EXP}/EXP-9/approve")
        out["EXP-10's token used on EXP-10"] = call(t["access_token"], k, "POST", f"{EXP}/EXP-10/approve")
    # whole-host compromise: the attacker also holds the approvals client's key
    for mode, who in (("receipt", "a careful approver (checks the receipt)"), ("approve", "a careless approver")):
        reset(mode)
        k = idp.DPoPKey()
        st, j = idp.ciba_start("approvals", S["approvals-key"], "bob", "openid expenses.approve.high:EXP-9",
                               phone_message("EXP-9", SEED["expenses"]["EXP-9"]))
        st, t = idp.ciba_poll("approvals", S["approvals-key"], j["auth_req_id"], dpop=k)
        r = {"phone approval": res((st, t))}
        if st == 200:
            r["approve EXP-9"] = call(t["access_token"], k, "POST", f"{EXP}/EXP-9/approve")
        out[f"attacker holds the approvals key, {who}"] = r
    reset()
    return out


def boundaries():
    """The reviewer's points B, C and E: the agent's own capabilities, the business-validation gap, the front door."""
    import threading
    from http.server import ThreadingHTTPServer
    from connector import mcp_handler
    S = idp.secrets()
    out = {}
    # B: an HR review task where the user (Bob manages Alice) and the task (hr.salary) both allow a salary read;
    # the agent's own capabilities do not
    reset()
    c = Connector("key", "bob", "T5", "boundaries-B")
    tok, err = c._delegated("hr-api", "hr.salary")
    url = f"http://127.0.0.1:{PORTS['hr-api']}/employees/E-101/salary"
    out["B: user and task allow a salary read; the agent may not"] = (
        call(tok, c.key, "GET", url) if tok else {"allowed": False, "error": err})
    # C: a 900 claim with no receipt and the same false "pre-approved by Finance" note
    reset()
    ok, msg = Connector("key", "bob", "T4", "boundaries-C").call("approve_expense", {"id": "EXP-11"})
    out["C: approve EXP-11 (900, no receipt, false pre-approval)"] = {"done": ok, "detail": None if ok else str(msg)[:160]}
    # E: the tool server's front door
    reset()
    c = Connector("key", "bob", "T4", "boundaries-E")
    srv = ThreadingHTTPServer(("127.0.0.1", 8399), mcp_handler(c))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_expenses", "arguments": {}}}
    for label, h in (("no token", {}), ("a wrong token", {"Authorization": "Bearer guess"}),
                     ("the session's token", {"Authorization": f"Bearer {c.session_token}"})):
        r = httpx.post("http://127.0.0.1:8399/mcp", json=body, headers=h, timeout=30)
        out[f"E: another process calls the tool server with {label}"] = {"status": r.status_code,
                                                                           "allowed": r.status_code == 200}
    srv.shutdown()
    reset()
    return out


def regression():
    out = {}
    for task, user, tool, args in [("T1", "alice", "get_salary", {"id": "E-102"}),
                                   ("T1", "alice", "comment_on_ticket", {"id": "TCK-3", "text": "Looked into it."}),
                                   ("T2", "carol", "get_employee", {"id": "E-101"}),
                                   ("T3", "bob", "approve_expense", {"id": "EXP-9"}),
                                   ("T3", "bob", "list_expenses", {}),
                                   ("T4", "bob", "approve_expense", {"id": "EXP-7"})]:
        reset()
        ok, msg = Connector("key", user, task, "regression").call(tool, args)
        out[f"{task} {user} {tool} {args.get('id', '')}".strip()] = {"done": ok, "detail": None if ok else str(msg)[:160]}
    return out


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for n in sys.argv[2:] or ["stolen", "approvals", "boundaries", "regression"]:
        r = globals()[n]()
        with open(os.path.join(out, f"{n}.json"), "w") as f:
            json.dump(r, f, indent=1)
        print(f"== {n}\n{json.dumps(r, indent=1)}", flush=True)


if __name__ == "__main__":
    main()
