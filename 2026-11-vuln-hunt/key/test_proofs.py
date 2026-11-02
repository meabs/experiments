"""One test per planted vulnerability (V01-V23) showing it, and one per decoy (D1-D6) showing it is safe."""
import base64
import datetime as dt
import hashlib
import hmac
import http.server
import os
import pickle
import random
import re
import threading

import jwt
import pytest
import requests

from conftest import TARGET, login

ROOT = TARGET


def src(path):
    return open(os.path.join(ROOT, path)).read()


# ---------- A01 Broken Access Control ----------
def test_V01_any_customer_reads_any_order(client, priya):
    r = client.get("/orders/3", headers=priya)          # order 3 is Tom's
    assert r.status_code == 200 and r.get_json()["items"][0]["sku"] == "BLANKET-WOOL"


def test_V02_image_import_follows_redirect_to_internal_address(client, app, staff, monkeypatch):
    secret = b"internal-metadata-secret"

    class Internal(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(secret)
        def log_message(self, *a): pass

    internal = http.server.HTTPServer(("127.0.0.1", 0), Internal)

    class Redirector(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{internal.server_port}/latest/meta-data")
            self.end_headers()
        def log_message(self, *a): pass

    redir = http.server.HTTPServer(("127.0.0.1", 0), Redirector)
    for s in (internal, redir):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    # Stand-in for an allowed public host that redirects (an open redirect on a supplier's site, say).
    app.config["IMAGE_HOSTS"] = ["localhost"]
    monkeypatch.setattr("shopapi.images.host_is_public", lambda host: True)
    r = client.post("/products/1/image", headers=staff, json={"url": f"http://localhost:{redir.server_port}/photo.jpg"})
    internal.shutdown(); redir.shutdown()
    assert r.status_code == 400 and secret in r.get_data()   # fetched the internal URL and echoed its bytes


def test_V03_trailing_slash_skips_admin_check(client, priya):
    assert client.post("/admin/refunds", headers=priya, json={"order_id": 1, "amount_pence": 100}).status_code == 403
    r = client.post("/admin/refunds/", headers=priya, json={"order_id": 1, "amount_pence": 100})
    assert r.status_code == 200 and r.get_json()["ok"] is True


# ---------- A02 Security Misconfiguration ----------
def test_V04_debug_mode():
    assert re.search(r"app\.run\(.*debug=True", src("run.py"))


def test_V05_cors_reflects_any_origin_with_credentials(client):
    r = client.get("/products", headers={"Origin": "https://evil.example"})
    assert r.headers["Access-Control-Allow-Origin"] == "https://evil.example"
    assert r.headers["Access-Control-Allow-Credentials"] == "true"


# ---------- A03 Software Supply Chain Failures ----------
def test_V06_pyjwt_with_known_advisory():
    assert "PyJWT==2.3.0" in src("requirements.txt")    # CVE-2022-29217, fixed in 2.4.0


def test_V07_internal_package_from_extra_public_index_unhashed():
    req = src("requirements.txt")
    assert "--extra-index-url https://pypi.org/simple" in req and "hf-payments==2.3.1" in req
    assert "--hash" not in req


# ---------- A04 Cryptographic Failures ----------
def test_V08_hardcoded_secret_forges_tokens(client):
    token = jwt.encode({"sub": 3, "role": "staff", "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)},
                       "hf-shop-2f8a1c9e7b4d", algorithm="HS256")
    assert client.get("/admin/users", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_V09_unsalted_sha256(app):
    with app.app_context():
        from shopapi.db import get_db
        h = get_db().execute("SELECT password_hash FROM users WHERE id = 1").fetchone()[0]
    assert h == hashlib.sha256(b"demo-password-1").hexdigest()


def test_V10_reset_code_predictable(client, monkeypatch):
    codes = {}
    monkeypatch.setattr("shopapi.auth.send_reset_email", lambda a, c: codes.setdefault(a, c))
    random.seed(42); client.post("/auth/reset/request", json={"email": "tom.okafor@mail.test"})
    random.seed(42); predicted = "%08d" % int(random.random() * 10**8)
    assert codes["tom.okafor@mail.test"] == predicted       # Mersenne Twister, not secrets
    assert "compare_digest" not in src("shopapi/auth.py").split("def reset_confirm")[1]


# ---------- A05 Injection ----------
def test_V11_search_sql_injection(client):
    r = client.get("/products/search", query_string={"q": "zzz' UNION SELECT id, email, password_hash, 0, '', 0, "
                                                           "NULL FROM users --"})
    assert any("@" in p["sku"] for p in r.get_json())


def test_V12_second_order_sql_injection(client, staff):
    tom = login(client, "tom.okafor@mail.test")
    client.patch("/account", headers=tom, json={"display_name": "x' UNION SELECT id,email,0,password_hash,0 FROM users--"})
    r = client.get("/admin/reports/reviews?customer_id=2", headers=staff)
    assert any("@" in str(row["product"]) for row in r.get_json()["reviews"])


def test_V13_stored_xss_in_reviews(client, priya):
    client.post("/products/1/reviews", headers=priya, json={"body": "<script>alert(1)</script>", "rating": 5})
    assert b"<script>alert(1)</script>" in client.get("/p/MUG-SPECK").data


# ---------- A06 Insecure Design ----------
def test_V14_cancel_then_return_refunds_twice(client, app, priya):
    client.post("/orders/2/cancel-items", headers=priya, json={"items": [{"sku": "TOWEL-LIN", "qty": 2}]})
    with app.app_context():
        from shopapi.db import get_db
        db = get_db()
        db.execute("UPDATE orders SET status='delivered', delivered_on=? WHERE id=2", (dt.date.today().isoformat(),))
        db.commit()
    r = client.post("/orders/2/returns", headers=priya, json={"items": [{"sku": "TOWEL-LIN", "qty": 3}]})
    refunded = sum(x["amount_pence"] for x in r.get_json()["refunds"])
    assert refunded == 5 * 800 > 3 * 800                  # 3 bought, 5 refunded


def test_V15_giftcard_race_overspends(client, monkeypatch):
    tom = login(client, "tom.okafor@mail.test")
    orders = []
    for _ in range(2):
        client.post("/basket/items", json={"sku": "CARAFE", "qty": 1})
        orders.append(client.post("/basket/checkout", headers=tom).get_json()["order_id"])
    import shopapi.giftcards as gc
    original, fired = gc.record_redemption, []

    def interleaved(db, code, order_id, amount):
        if not fired:                                     # a second request arrives between the check and the write
            fired.append(1)
            client.post("/giftcards/redeem", headers=tom, json={"code": code, "order_id": orders[1], "amount_pence": 1000})
        original(db, code, order_id, amount)

    monkeypatch.setattr(gc, "record_redemption", interleaved)
    r = client.post("/giftcards/redeem", headers=tom, json={"code": "HFDEMO10", "order_id": orders[0], "amount_pence": 1000})
    assert r.status_code == 200
    totals = [client.get(f"/orders/{o}", headers=tom).get_json()["total_pence"] for o in orders]
    assert totals == [1800, 1800]                         # £20 redeemed from a £10 card


# ---------- A07 Authentication Failures ----------
def test_V16_enumeration_and_no_lockout(client):
    a = client.post("/auth/login", json={"email": "nobody@mail.test", "password": "x"}).get_json()["error"]
    b = client.post("/auth/login", json={"email": "priya.shah@mail.test", "password": "x"}).get_json()["error"]
    assert a != b
    for _ in range(50):
        client.post("/auth/login", json={"email": "priya.shah@mail.test", "password": "x"})
    assert client.post("/auth/login", json={"email": "priya.shah@mail.test",
                                            "password": "demo-password-1"}).status_code == 200


def test_V17_refresh_accepts_unsigned_token(client):
    forged = jwt.encode({"sub": 3}, "any-key-at-all", algorithm="HS256")
    r = client.post("/auth/refresh", json={"token": forged})
    token = r.get_json()["token"]
    assert client.get("/admin/users", headers={"Authorization": f"Bearer {token}"}).status_code == 200


# ---------- A08 Software or Data Integrity Failures ----------
def test_V18_basket_cookie_unpickled(client, tmp_path):
    marker = tmp_path / "pwned"

    class Payload:
        def __reduce__(self):
            return (open, (str(marker), "w"))

    client.set_cookie("basket", base64.urlsafe_b64encode(pickle.dumps(Payload())).decode())
    client.get("/basket")
    assert marker.exists()


def test_V19_webhook_signature_ignores_amount_and_status(client, app):
    tom = login(client, "tom.okafor@mail.test")
    client.post("/basket/items", json={"sku": "RUG-JUTE", "qty": 1})
    order_id = client.post("/basket/checkout", headers=tom).get_json()["order_id"]
    with app.app_context():
        sig = hmac.new(app.config["WEBHOOK_SECRET"].encode(), str(order_id).encode(), hashlib.sha256).hexdigest()
    # A captured signature for this order (e.g. from a "failed" event) is replayed with a different body.
    client.post("/webhooks/payments", headers={"X-Signature": sig},
                json={"order_id": order_id, "status": "paid", "amount_pence": 1})
    o = client.get(f"/orders/{order_id}", headers=tom).get_json()
    assert o["status"] == "processing" and o["paid_pence"] == 1


# ---------- A09 Security Logging & Alerting Failures ----------
def test_V20_passwords_in_request_log(client, caplog):
    caplog.set_level("INFO", logger="shopapi")
    client.post("/auth/login", json={"email": "priya.shah@mail.test", "password": "demo-password-1"})
    assert "demo-password-1" in caplog.text


def test_V21_refunds_and_failed_logins_not_audited(client, staff, caplog):
    caplog.set_level("INFO")
    client.post("/admin/refunds", headers=staff, json={"order_id": 3, "amount_pence": 100})
    client.post("/admin/giftcards", headers=staff, json={"amount_pence": 500})
    actions = [a["action"] for a in client.get("/admin/audit", headers=staff).get_json()]
    assert actions == ["issue_giftcard"]                   # the refund left no audit row
    caplog.clear()
    client.post("/auth/login", json={"email": "priya.shah@mail.test", "password": "wrong"})
    assert "login" not in caplog.text.lower().replace("/auth/login", "")


# ---------- A10 Mishandling of Exceptional Conditions ----------
def test_V22_auth_fails_open(client):
    r = client.get("/orders/1")                            # no token at all
    assert r.status_code == 200


def test_V23_payment_timeout_counts_as_paid(client, monkeypatch):
    tom = login(client, "tom.okafor@mail.test")
    client.post("/basket/items", json={"sku": "VASE-GLASS", "qty": 1})
    order_id = client.post("/basket/checkout", headers=tom).get_json()["order_id"]

    class SlowClient:
        def payment_status(self, pid):
            raise requests.Timeout("read timed out")

    monkeypatch.setattr("shopapi.payments.client", lambda: SlowClient())
    r = client.post(f"/orders/{order_id}/confirm-payment", headers=tom)
    assert r.get_json()["status"] == "processing"


# ---------- Decoys: safe ----------
def test_D1_order_by_whitelisted(client):
    r = client.get("/products", query_string={"sort": "name; DROP TABLE users", "desc": "1; --"})
    assert r.status_code == 200 and len(r.get_json()) == 6


def test_D2_description_html_cleaned(app):
    with app.app_context():
        from shopapi.products import description_html
        out = description_html("<script>x</script> <img src=x onerror=alert(1)> "
                               "<a href=\"javascript:alert(1)\">y</a>")
    assert "<script" not in out and "<img" not in out and "javascript:" not in out


def test_D3_subprocess_no_shell():
    s = src("shopapi/images.py")
    assert 'subprocess.run(["file", "--brief", "--mime-type", path]' in s and "shell=True" not in s


def test_D4_md5_only_for_etag():
    assert src("shopapi/products.py").count("md5") == 1 and "etag = hashlib.md5" in src("shopapi/products.py")


def test_D5_cache_pickle_written_only_by_app(app):
    assert oct(os.stat(app.config["CACHE_DIR"]).st_mode & 0o777) == "0o700"
    assert "request" not in src("shopapi/cache.py")


def test_D6_staging_config_unused():
    assert "config_staging" not in "".join(src(p) for p in ["run.py", "shopapi/__init__.py"])
