"""Builds the fictional company's identity setup ("acme" realm) in a local Keycloak through its admin REST API.

Usage: uv run --with httpx python3 -I src/realm.py
Deletes and recreates the realm each time, so every run starts from the same state. Writes results/realm-objects.json:
the admin objects created, grouped by the setup that needs them (used for the configuration-effort count).

People (passwords are local test values):
  alice   engineer            roles employee
  bob     engineering manager roles employee, manager    (manages alice and dave)
  carol   contractor          roles contractor
  dave    engineer, leaver    roles employee             (disabled mid-task in the leaver scenario)
Services: hr-api, expenses-api, tickets-api (audiences only; they validate tokens themselves, see services.py).
API scopes, each adding its service as audience: hr.read hr.salary expenses.read expenses.approve tickets.read
tickets.write.
Clients, one per setup:
  1 shared key   none (the services hold a static key; see services.py)
  2 passthrough  staff-portal: the user's own login token, all API scopes by default, realm lifetime (1 hour)
  3 service acct assistant-svc: client credentials; roles hr + finance-approver (the union every user's tasks need)
  4 delegated    assistant: user signs in to the agent app and consents to delegation; token exchange (with `act`)
                 per service with only the task's scopes; DPoP-bound; 2-minute tokens; exchange may only narrow.
  probe only     assistant-std (plain exchange) and expenses-bot (a sub-agent), for the chain and widening checks.
"""
import json, os, sys

import httpx

KC = os.environ.get("KC_URL", "http://127.0.0.1:8180")
REALM = "acme"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "setup", "local-secrets.json")  # local only, git-ignored
API_SCOPES = {"hr.read": "hr-api", "hr.salary": "hr-api", "expenses.read": "expenses-api",
              "expenses.approve": "expenses-api", "tickets.read": "tickets-api", "tickets.write": "tickets-api"}
PEOPLE = {"alice": ["employee"], "bob": ["employee", "manager"], "carol": ["contractor"], "dave": ["employee"]}
USER_PASSWORD = "local-test-only"
REDIRECT = "http://127.0.0.1:9/callback"  # never served: the scripted browser reads the code from the redirect

objects = {"common": [], "2": [], "3": [], "4": [], "probe": []}


def admin():
    r = httpx.post(f"{KC}/realms/master/protocol/openid-connect/token",
                   data={"grant_type": "password", "client_id": "admin-cli", "username": "admin",
                         "password": os.environ.get("KC_ADMIN_PASSWORD", "admin-local-only")})
    r.raise_for_status()
    return httpx.Client(base_url=f"{KC}/admin/realms", headers={"Authorization": f"Bearer {r.json()['access_token']}"},
                        timeout=30)


def ok(r):
    if r.status_code >= 400:
        sys.exit(f"{r.request.method} {r.request.url} -> {r.status_code} {r.text}")
    return r


def made(group, kind, name):
    objects[group].append(f"{kind}:{name}")


def client(c, group, cid, **rep):
    rep = {"clientId": cid, "protocol": "openid-connect", "enabled": True, "standardFlowEnabled": False,
           "directAccessGrantsEnabled": False, "serviceAccountsEnabled": False, "publicClient": False,
           "fullScopeAllowed": True, **rep}
    ok(c.post(f"/{REALM}/clients", json=rep))
    made(group, "client", cid)
    return ok(c.get(f"/{REALM}/clients", params={"clientId": cid})).json()[0]


def scope_ids(c):
    return {s["name"]: s["id"] for s in ok(c.get(f"/{REALM}/client-scopes")).json()}


def set_scopes(c, group, cl, default=(), optional=()):
    ids = scope_ids(c)
    # drop the realm's default API-free scopes we don't want? keep them (profile, roles, ...); only add API scopes
    for kind, names in (("default-client-scopes", default), ("optional-client-scopes", optional)):
        for n in names:
            ok(c.put(f"/{REALM}/clients/{cl['id']}/{kind}/{ids[n]}"))
            made(group, kind.split("-")[0] + "-scope", f"{cl['clientId']}:{n}")


def audience_scope(c, group, name, audience):
    ok(c.post(f"/{REALM}/client-scopes", json={
        "name": name, "protocol": "openid-connect",
        "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"},
        "protocolMappers": [{"name": f"aud-{audience}", "protocol": "openid-connect",
                             "protocolMapper": "oidc-audience-mapper",
                             "config": {"included.client.audience": audience, "access.token.claim": "true",
                                        "id.token.claim": "false"}}]}))
    made(group, "client-scope", name)


def main():
    c = admin()
    if c.get(f"/{REALM}").status_code == 200:
        ok(c.delete(f"/{REALM}"))
    ok(c.post("", json={"realm": REALM, "enabled": True, "accessTokenLifespan": 3600,
                        "ssoSessionIdleTimeout": 28800, "ssoSessionMaxLifespan": 36000}))
    made("common", "realm", REALM)
    for role in ("employee", "manager", "contractor", "hr", "finance-approver"):
        ok(c.post(f"/{REALM}/roles", json={"name": role}))
        made("common", "role", role)
    roles = {r["name"]: r for r in ok(c.get(f"/{REALM}/roles")).json()}
    for user, rs in PEOPLE.items():
        ok(c.post(f"/{REALM}/users", json={
            "username": user, "enabled": True, "email": f"{user}@acme.example", "emailVerified": True,
            "firstName": user.title(), "lastName": "Example",
            "credentials": [{"type": "password", "value": USER_PASSWORD, "temporary": False}]}))
        uid = ok(c.get(f"/{REALM}/users", params={"username": user, "exact": "true"})).json()[0]["id"]
        ok(c.post(f"/{REALM}/users/{uid}/role-mappings/realm", json=[roles[r] for r in rs]))
        made("common", "user", user)
    for api in sorted(set(API_SCOPES.values())):
        client(c, "common", api, bearerOnly=False)
    for name, aud in API_SCOPES.items():
        audience_scope(c, "common", name, aud)

    secrets = {}
    # Setup 2: the user's own token, valid at every service, passed straight through by the agent's tools.
    portal = client(c, "2", "staff-portal", publicClient=True, directAccessGrantsEnabled=True)
    set_scopes(c, "2", portal, default=list(API_SCOPES))

    # Setup 3: the agent's own service account, holding the union of rights its users' tasks need.
    svc = client(c, "3", "assistant-svc", serviceAccountsEnabled=True)
    set_scopes(c, "3", svc, default=list(API_SCOPES))
    sa = ok(c.get(f"/{REALM}/clients/{svc['id']}/service-account-user")).json()
    ok(c.post(f"/{REALM}/users/{sa['id']}/role-mappings/realm",
              json=[roles["employee"], roles["hr"], roles["finance-approver"]]))
    made("3", "role-mapping", "service-account-assistant-svc:employee,hr,finance-approver")
    secrets["assistant-svc"] = ok(c.get(f"/{REALM}/clients/{svc['id']}/client-secret")).json()["value"]

    # Setup 4: the user signs in to the agent app and consents to it acting for them (Keycloak's preview delegation,
    # RFC 8693 `act` claim); the app exchanges that token for one short-lived, DPoP-bound token per service carrying
    # only the task's scopes. Exchange may only narrow scopes (client policy below).
    audience_scope(c, "4", "delegate.expenses-bot", "expenses-bot")
    secrets["assistant"] = delegation(c)
    enforce_downscope(c, True)

    # Probe-only clients (scenarios.py, "chain" and "widening"): plain standard token exchange without delegation or
    # DPoP, and a sub-agent the assistant hands an expenses job to.
    std = client(c, "probe", "assistant-std", directAccessGrantsEnabled=True, attributes={
        "standard.token.exchange.enabled": "true", "access.token.lifespan": "120"})
    set_scopes(c, "probe", std, optional=list(API_SCOPES) + ["delegate.expenses-bot"])
    secrets["assistant-std"] = ok(c.get(f"/{REALM}/clients/{std['id']}/client-secret")).json()["value"]
    bot = client(c, "probe", "expenses-bot", serviceAccountsEnabled=True, attributes={
        "standard.token.exchange.enabled": "true", "access.token.lifespan": "120"})
    set_scopes(c, "probe", bot, optional=["expenses.read", "expenses.approve", "hr.salary"])
    secrets["expenses-bot"] = ok(c.get(f"/{REALM}/clients/{bot['id']}/client-secret")).json()["value"]

    with open(SECRETS, "w") as f:
        json.dump(secrets, f, indent=1)
    os.chmod(SECRETS, 0o600)
    with open(os.path.join(ROOT, "results", "realm-objects.json"), "w") as f:
        json.dump(objects, f, indent=1)
    print({k: len(v) for k, v in objects.items()})


def delegation(c):
    """Setup 4's agent client with Keycloak's preview delegation: the user consents at sign-in to the agent acting for
    them (`may_act`); the agent exchanges with its own token as actor_token and gets `act`. Needs FGAP v2, consent
    on every sign-in, and a service account."""
    rep = ok(c.get(f"/{REALM}")).json()
    rep["adminPermissionsEnabled"] = True
    ok(c.put(f"/{REALM}", json=rep))
    made("4", "realm-setting", "adminPermissionsEnabled")
    d = client(c, "4", "assistant", standardFlowEnabled=True, serviceAccountsEnabled=True, consentRequired=True,
               redirectUris=[REDIRECT], attributes={"standard.token.exchange.enabled": "true",
                                                    "dpop.bound.access.tokens": "true", "access.token.lifespan": "120"})
    set_scopes(c, "4", d, optional=list(API_SCOPES) + ["delegate.expenses-bot"])
    ap = ok(c.get(f"/{REALM}/clients", params={"clientId": "admin-permissions"})).json()[0]["id"]
    rs = f"/{REALM}/clients/{ap}/authz/resource-server"
    ok(c.post(f"{rs}/policy/client", json={"name": "agents-that-may-act", "clients": [d["id"]],
                                           "logic": "POSITIVE"}))
    pol = ok(c.get(f"{rs}/policy", params={"name": "agents-that-may-act"})).json()[0]["id"]
    ok(c.post(f"{rs}/permission/scope", json={"name": "assistant may delegate for all users", "resourceType": "Users",
                                              "scopes": ["delegate"], "policies": [pol],
                                              "decisionStrategy": "UNANIMOUS"}))
    made("4", "permission", "Users:delegate -> assistant")
    return ok(c.get(f"/{REALM}/clients/{d['id']}/client-secret")).json()["value"]


def enforce_downscope(c, on):
    """Client policy that only lets token exchange narrow scopes, never widen them (not on by default in Keycloak)."""
    ok(c.put(f"/{REALM}/client-policies/profiles", json={"profiles": [{
        "name": "downscope-only", "executors": [{"executor": "downscope-assertion-grant-enforcer",
                                                 "configuration": {}}]}]}))
    ok(c.put(f"/{REALM}/client-policies/policies", json={"policies": [{
        "name": "exchange-downscope-only", "enabled": on, "profiles": ["downscope-only"],
        "conditions": [{"condition": "any-client", "configuration": {}}]}]}))
    if on and "client-policy:exchange-downscope-only" not in objects["4"]:
        made("4", "client-policy", "exchange-downscope-only")


if __name__ == "__main__":
    main()
