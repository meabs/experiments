"""Talks to the local Keycloak: sign-in, token exchange, refresh, CIBA ("approve on your phone"), DPoP proofs, and the
two ways a client proves who it is (a client secret, or a JWT signed with its private key).

A client credential `cred` is either a string (a client secret) or {"pem": ..., "kid": ...} (a private key, for
private_key_jwt). Adapted from 2026-10-agent-identity/src/idp.py.
"""
import base64, hashlib, json, os, time, uuid

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import ec

KC = os.environ.get("KC_URL", "http://127.0.0.1:8180")
REALM = "acme"
ISSUER = f"{KC}/realms/{REALM}"
TOKEN_URL = f"{ISSUER}/protocol/openid-connect/token"
CIBA_URL = f"{ISSUER}/protocol/openid-connect/ext/ciba/auth"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_PASSWORD = "local-test-only"
TE = "urn:ietf:params:oauth:grant-type:token-exchange"
AT = "urn:ietf:params:oauth:token-type:access_token"
CIBA = "urn:openid:params:grant-type:ciba"
JWT_BEARER = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
REDIRECT = "http://127.0.0.1:9/callback"


def secrets():
    with open(os.path.join(ROOT, "setup", "local-secrets.json")) as f:
        return json.load(f)


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def claims(token):
    return jwt.decode(token, options={"verify_signature": False})


def assertion(client_id, key):
    """A private_key_jwt client assertion: short-lived, single-use (jti), signed with the client's private key."""
    now = int(time.time())
    return jwt.encode({"iss": client_id, "sub": client_id, "aud": ISSUER, "jti": str(uuid.uuid4()), "iat": now,
                       "exp": now + 60}, key["pem"], algorithm="ES256", headers={"kid": key["kid"]})


def client_auth(client_id, cred):
    """Form fields proving who the client is."""
    if cred is None:
        return {"client_id": client_id}
    if isinstance(cred, str):
        return {"client_id": client_id, "client_secret": cred}
    if "assertion" in cred:  # a captured assertion, replayed as is
        return {"client_id": client_id, "client_assertion_type": JWT_BEARER, "client_assertion": cred["assertion"]}
    return {"client_id": client_id, "client_assertion_type": JWT_BEARER, "client_assertion": assertion(client_id, cred)}


class DPoPKey:
    """An agent's proof-of-possession key. Tokens bound to it are useless to anyone who only copies the token."""

    def __init__(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        n = self.key.public_key().public_numbers()
        self.jwk = {"kty": "EC", "crv": "P-256", "x": b64(n.x.to_bytes(32, "big")), "y": b64(n.y.to_bytes(32, "big"))}

    def proof(self, method, url, access_token=None):
        body = {"htm": method, "htu": url, "iat": int(time.time()), "jti": str(uuid.uuid4())}
        if access_token:
            body["ath"] = b64(hashlib.sha256(access_token.encode()).digest())
        return jwt.encode(body, self.key, algorithm="ES256", headers={"typ": "dpop+jwt", "jwk": self.jwk})


def _post(url, data, dpop=None):
    headers = {"DPoP": dpop.proof("POST", url)} if dpop else {}
    r = httpx.post(url, data=data, headers=headers, timeout=30)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"error": r.text[:300]}


def browser_login(client_id, cred, user, scope, consent=True, dpop=None):
    """The real sign-in: authorisation-code flow with PKCE, filling Keycloak's login form and consent screen as a person
    in a browser would. Returns (status, token response, consent screen shown?)."""
    import re, html
    verifier = b64(os.urandom(32))
    challenge = b64(hashlib.sha256(verifier.encode()).digest())
    b = httpx.Client(follow_redirects=False, timeout=30)
    r = b.get(f"{ISSUER}/protocol/openid-connect/auth", params={
        "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT, "scope": scope,
        "state": "s", "code_challenge": challenge, "code_challenge_method": "S256"})
    form = lambda page: httpx.URL(KC).join(html.unescape(re.search(r'<form[^>]*action="([^"]+)"', page).group(1)))
    # Keycloak marks its cookies Secure; this local test runs over plain http, so send them back explicitly
    jar = lambda: {"Cookie": "; ".join(f"{k}={v}" for k, v in b.cookies.items())}
    if r.status_code != 200:
        return r.status_code, {"error": r.headers.get("location", r.text[:300])}, False
    r = b.post(form(r.text), data={"username": user, "password": USER_PASSWORD}, headers=jar())
    while r.status_code in (302, 303) and r.headers["location"].startswith(KC):
        r = b.get(r.headers["location"], headers=jar())
    shown = False
    if r.status_code == 200 and 'name="accept"' in r.text:
        shown = True
        code = re.search(r'name="code" value="([^"]+)"', r.text)
        data = {"accept" if consent else "cancel": "Yes" if consent else "No"}
        if code:
            data["code"] = html.unescape(code.group(1))
        r = b.post(form(r.text), data=data, headers=jar())
    loc = r.headers.get("location", "")
    m = re.search(r"[?&]code=([^&]+)", loc)
    if not m:
        return r.status_code, {"error": loc or r.text[:300]}, shown
    st, j = _post(TOKEN_URL, {"grant_type": "authorization_code", "code": m.group(1), "redirect_uri": REDIRECT,
                              "code_verifier": verifier, **client_auth(client_id, cred)}, dpop)
    return st, j, shown


def client_credentials(client_id, cred, dpop=None):
    return _post(TOKEN_URL, {"grant_type": "client_credentials", **client_auth(client_id, cred)}, dpop)


def exchange(client_id, cred, subject_token, audience=None, scope=None, dpop=None, actor_token=None):
    d = {"grant_type": TE, "subject_token": subject_token, "subject_token_type": AT, "requested_token_type": AT,
         **client_auth(client_id, cred)}
    if audience:
        d["audience"] = audience
    if scope:
        d["scope"] = scope
    if actor_token:
        d["actor_token"], d["actor_token_type"] = actor_token, AT
    return _post(TOKEN_URL, d, dpop)


def refresh(client_id, cred, refresh_token, dpop=None):
    return _post(TOKEN_URL, {"grant_type": "refresh_token", "refresh_token": refresh_token,
                             **client_auth(client_id, cred)}, dpop)


def ciba_start(client_id, cred, user, scope, message):
    """Asks Keycloak to have the user confirm on their own device; returns (status, {auth_req_id, ...})."""
    return _post(CIBA_URL, {"login_hint": user, "scope": scope, "binding_message": message,
                            **client_auth(client_id, cred)})


def ciba_poll(client_id, cred, auth_req_id, dpop=None, wait=30):
    """Polls until the user has answered on their device (or the wait runs out)."""
    t0 = time.time()
    while True:
        st, j = _post(TOKEN_URL, {"grant_type": CIBA, "auth_req_id": auth_req_id, **client_auth(client_id, cred)},
                      dpop)
        if st == 200 or j.get("error") not in ("authorization_pending", "slow_down") or time.time() - t0 > wait:
            return st, j
        time.sleep(1)


def _admin():
    r = httpx.post(f"{KC}/realms/master/protocol/openid-connect/token",
                   data={"grant_type": "password", "client_id": "admin-cli", "username": "admin",
                         "password": os.environ.get("KC_ADMIN_PASSWORD", "admin-local-only")})
    return httpx.Client(base_url=f"{KC}/admin/realms/{REALM}",
                        headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=30)
