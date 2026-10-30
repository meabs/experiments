"""Talks to the local Keycloak: logins, client credentials, token exchange, DPoP proofs, admin offboarding."""
import base64, hashlib, json, os, time, uuid

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import ec

KC = os.environ.get("KC_URL", "http://127.0.0.1:8180")
REALM = "acme"
TOKEN_URL = f"{KC}/realms/{REALM}/protocol/openid-connect/token"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_PASSWORD = "local-test-only"
TE = "urn:ietf:params:oauth:grant-type:token-exchange"
AT = "urn:ietf:params:oauth:token-type:access_token"


def secrets():
    with open(os.path.join(ROOT, "setup", "local-secrets.json")) as f:
        return json.load(f)


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def claims(token):
    return jwt.decode(token, options={"verify_signature": False})


class DPoPKey:
    """An agent's proof-of-possession key. Tokens bound to it are useless to anyone who only copies the token."""

    def __init__(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        n = self.key.public_key().public_numbers()
        self.jwk = {"kty": "EC", "crv": "P-256", "x": b64(n.x.to_bytes(32, "big")), "y": b64(n.y.to_bytes(32, "big"))}

    def thumbprint(self):
        canon = json.dumps({k: self.jwk[k] for k in ("crv", "kty", "x", "y")}, separators=(",", ":"))
        return b64(hashlib.sha256(canon.encode()).digest())

    def proof(self, method, url, access_token=None):
        body = {"htm": method, "htu": url, "iat": int(time.time()), "jti": str(uuid.uuid4())}
        if access_token:
            body["ath"] = b64(hashlib.sha256(access_token.encode()).digest())
        return jwt.encode(body, self.key, algorithm="ES256", headers={"typ": "dpop+jwt", "jwk": self.jwk})


def _token(data, dpop=None):
    headers = {"DPoP": dpop.proof("POST", TOKEN_URL)} if dpop else {}
    r = httpx.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    return r.status_code, r.json()


def user_login(client_id, user, secret=None, dpop=None, scope=None):
    """Stand-in for the browser sign-in (password grant; a real deployment would use the authorisation-code flow)."""
    d = {"grant_type": "password", "client_id": client_id, "username": user, "password": USER_PASSWORD}
    if secret:
        d["client_secret"] = secret
    if scope:
        d["scope"] = scope
    return _token(d, dpop)


REDIRECT = "http://127.0.0.1:9/callback"


def browser_login(client_id, secret, user, scope, consent=True, dpop=None):
    """The real sign-in: authorisation-code flow with PKCE, filling Keycloak's login form and (if shown) the consent
    screen, as a person in a browser would. Returns (status, token response, consent screen shown?)."""
    import re, html
    verifier = b64(os.urandom(32))
    challenge = b64(hashlib.sha256(verifier.encode()).digest())
    b = httpx.Client(follow_redirects=False, timeout=30)
    r = b.get(f"{KC}/realms/{REALM}/protocol/openid-connect/auth", params={
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
    st, j = _token({"grant_type": "authorization_code", "client_id": client_id, "client_secret": secret,
                    "code": m.group(1), "redirect_uri": REDIRECT, "code_verifier": verifier}, dpop)
    return st, j, shown


def client_credentials(client_id, secret, dpop=None):
    return _token({"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret}, dpop)


def exchange(client_id, secret, subject_token, audience=None, scope=None, dpop=None, actor_token=None):
    d = {"grant_type": TE, "client_id": client_id, "client_secret": secret, "subject_token": subject_token,
         "subject_token_type": AT, "requested_token_type": AT}
    if audience:
        d["audience"] = audience
    if scope:
        d["scope"] = scope
    if actor_token:
        d["actor_token"], d["actor_token_type"] = actor_token, AT
    return _token(d, dpop)


def refresh(client_id, secret, refresh_token, dpop=None):
    return _token({"grant_type": "refresh_token", "client_id": client_id, "client_secret": secret,
                   "refresh_token": refresh_token}, dpop)


def _admin():
    r = httpx.post(f"{KC}/realms/master/protocol/openid-connect/token",
                   data={"grant_type": "password", "client_id": "admin-cli", "username": "admin",
                         "password": os.environ.get("KC_ADMIN_PASSWORD", "admin-local-only")})
    return httpx.Client(base_url=f"{KC}/admin/realms/{REALM}",
                        headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=30)


def offboard(user):
    """What an identity team does when someone leaves: disable the account and end their sessions."""
    c = _admin()
    uid = c.get("/users", params={"username": user, "exact": "true"}).json()[0]["id"]
    c.put(f"/users/{uid}", json={"enabled": False}).raise_for_status()
    c.post(f"/users/{uid}/logout").raise_for_status()


def reinstate(user):
    c = _admin()
    uid = c.get("/users", params={"username": user, "exact": "true"}).json()[0]["id"]
    c.put(f"/users/{uid}", json={"enabled": True}).raise_for_status()
