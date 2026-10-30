"""Builds the "acme" realm for the hardening follow-up: setup 4 (delegated, task-scoped, DPoP-bound) from
2026-10-agent-identity, in two variants of client authentication, plus a separate approvals client.

Usage: uv run --with httpx --with cryptography python3 -I src/realm.py
Deletes and recreates the realm; writes setup/local-secrets.json (git-ignored: the client secret and the private keys)
and results/realm-objects.json.

People and services are as in 2026-10-agent-identity (alice, bob, carol, dave; hr-api, expenses-api, tickets-api).
Clients:
  assistant-secret  setup 4 exactly as in the first test: authenticates to Keycloak with a client secret
  assistant         the same, but authenticates with a signed JWT (private_key_jwt). Keycloak holds only the public
                    key; the private key stays with the tool server (in production, in a vault or hardware module)
  approvals         used only for CIBA ("approve on your phone"): no sign-in, no token exchange. It asks for the
                    parameterised scope expenses.approve.high:<claim id>, which the user must confirm on their own
                    device. Also private_key_jwt, with its own key.
The services require a token from `approvals`, with the matching claim id, for approvals over 1,000 (services.py).
"""
import json, os, sys

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

KC = os.environ.get("KC_URL", "http://127.0.0.1:8180")
REALM = "acme"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "setup", "local-secrets.json")  # local only, git-ignored
API_SCOPES = {"hr.read": "hr-api", "hr.salary": "hr-api", "expenses.read": "expenses-api",
              "expenses.approve": "expenses-api", "tickets.read": "tickets-api", "tickets.write": "tickets-api"}
PEOPLE = {"alice": ["employee"], "bob": ["employee", "manager"], "carol": ["contractor"], "dave": ["employee"]}
USER_PASSWORD = "local-test-only"
REDIRECT = "http://127.0.0.1:9/callback"  # never served: the scripted browser reads the code from the redirect

objects = {"common": [], "4-secret": [], "4-key": [], "approvals": []}


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


def set_scopes(c, group, cl, optional=()):
    ids = scope_ids(c)
    for n in optional:
        ok(c.put(f"/{REALM}/clients/{cl['id']}/optional-client-scopes/{ids[n]}"))
        made(group, "optional-scope", f"{cl['clientId']}:{n}")


def audience_scope(c, group, name, audience, dynamic=None):
    attrs = {"include.in.token.scope": "true", "display.on.consent.screen": "true"}
    if dynamic:  # Keycloak 26.8 parameterized scope (preview): "<name>:<parameter>", parameter checked by a regex
        attrs.update({"is.parameterized.scope": "true", "parameterized.scope.type": "custom",
                      "parameterized.scope.regexp": dynamic})
    ok(c.post(f"/{REALM}/client-scopes", json={
        "name": name, "protocol": "openid-connect", "attributes": attrs,
        "protocolMappers": [{"name": f"aud-{audience}", "protocol": "openid-connect",
                             "protocolMapper": "oidc-audience-mapper",
                             "config": {"included.client.audience": audience, "access.token.claim": "true",
                                        "id.token.claim": "false"}}]}))
    made(group, "client-scope", name)


def new_key():
    """An EC P-256 key pair: the private half (PEM) for the tool server, the public half (JWK) for Keycloak."""
    import base64, uuid
    k = ec.generate_private_key(ec.SECP256R1())
    n = k.public_key().public_numbers()
    b = lambda i: base64.urlsafe_b64encode(i.to_bytes(32, "big")).rstrip(b"=").decode()
    kid = str(uuid.uuid4())
    jwk = {"kty": "EC", "crv": "P-256", "x": b(n.x), "y": b(n.y), "kid": kid, "use": "sig", "alg": "ES256"}
    pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                          serialization.NoEncryption()).decode()
    return pem, kid, json.dumps({"keys": [jwk]})


def jwt_auth(jwks):
    """Client attributes for private_key_jwt with a registered public key."""
    return {"use.jwks.string": "true", "jwks.string": jwks, "token.endpoint.auth.signing.alg": "ES256"}


def main():
    c = admin()
    if c.get(f"/{REALM}").status_code == 200:
        ok(c.delete(f"/{REALM}"))
    ok(c.post("", json={"realm": REALM, "enabled": True, "accessTokenLifespan": 3600,
                        "ssoSessionIdleTimeout": 28800, "ssoSessionMaxLifespan": 36000,
                        "attributes": {"cibaBackchannelTokenDeliveryMode": "poll", "cibaExpiresIn": "120",
                                       "cibaInterval": "1", "cibaAuthRequestedUserHint": "login_hint"}}))
    made("common", "realm", REALM)
    made("approvals", "realm-setting", "CIBA policy (poll, 120 s, login_hint)")
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
        client(c, "common", api)
    for name, aud in API_SCOPES.items():
        audience_scope(c, "common", name, aud)

    secrets = {}
    # FGAP v2: needed for delegation (may_act / act)
    rep = ok(c.get(f"/{REALM}")).json()
    rep["adminPermissionsEnabled"] = True
    ok(c.put(f"/{REALM}", json=rep))
    made("common", "realm-setting", "adminPermissionsEnabled")
    base = dict(standardFlowEnabled=True, serviceAccountsEnabled=True, consentRequired=True, redirectUris=[REDIRECT])
    attrs = {"standard.token.exchange.enabled": "true", "dpop.bound.access.tokens": "true",
             "access.token.lifespan": "120"}
    sec = client(c, "4-secret", "assistant-secret", attributes=dict(attrs), **base)
    set_scopes(c, "4-secret", sec, optional=list(API_SCOPES))
    secrets["assistant-secret"] = ok(c.get(f"/{REALM}/clients/{sec['id']}/client-secret")).json()["value"]
    pem, kid, jwks = new_key()
    key = client(c, "4-key", "assistant", clientAuthenticatorType="client-jwt",
                 attributes={**attrs, **jwt_auth(jwks)}, **base)
    made("4-key", "client-auth", "private_key_jwt (public key registered)")
    set_scopes(c, "4-key", key, optional=list(API_SCOPES))
    secrets["assistant-key"] = {"pem": pem, "kid": kid}

    ap = ok(c.get(f"/{REALM}/clients", params={"clientId": "admin-permissions"})).json()[0]["id"]
    rs = f"/{REALM}/clients/{ap}/authz/resource-server"
    ok(c.post(f"{rs}/policy/client", json={"name": "agents-that-may-act", "clients": [sec["id"], key["id"]],
                                           "logic": "POSITIVE"}))
    pol = ok(c.get(f"{rs}/policy", params={"name": "agents-that-may-act"})).json()[0]["id"]
    ok(c.post(f"{rs}/permission/scope", json={"name": "the assistants may delegate for all users",
                                              "resourceType": "Users", "scopes": ["delegate"], "policies": [pol],
                                              "decisionStrategy": "UNANIMOUS"}))
    made("common", "permission", "Users:delegate -> assistant, assistant-secret")
    enforce_downscope(c)

    # approvals: CIBA only, a one-claim approval scope
    audience_scope(c, "approvals", "expenses.approve.high", "expenses-api", dynamic="EXP-[0-9]+")
    apem, akid, ajwks = new_key()
    appr = client(c, "approvals", "approvals", clientAuthenticatorType="client-jwt",
                  attributes={"oidc.ciba.grant.enabled": "true", "access.token.lifespan": "120",
                              "dpop.bound.access.tokens": "true", **jwt_auth(ajwks)})
    set_scopes(c, "approvals", appr, optional=["expenses.approve.high"])
    secrets["approvals-key"] = {"pem": apem, "kid": akid}

    with open(SECRETS, "w") as f:
        json.dump(secrets, f, indent=1)
    os.chmod(SECRETS, 0o600)
    with open(os.path.join(ROOT, "results", "realm-objects.json"), "w") as f:
        json.dump(objects, f, indent=1)
    print({k: len(v) for k, v in objects.items()})


def enforce_downscope(c):
    ok(c.put(f"/{REALM}/client-policies/profiles", json={"profiles": [{
        "name": "downscope-only", "executors": [{"executor": "downscope-assertion-grant-enforcer",
                                                 "configuration": {}}]}]}))
    ok(c.put(f"/{REALM}/client-policies/policies", json={"policies": [{
        "name": "exchange-downscope-only", "enabled": True, "profiles": ["downscope-only"],
        "conditions": [{"condition": "any-client", "configuration": {}}]}]}))
    made("common", "client-policy", "exchange-downscope-only")


if __name__ == "__main__":
    main()
