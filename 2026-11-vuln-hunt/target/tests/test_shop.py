from conftest import login


def test_health(client):
    assert client.get("/health").get_json() == {"ok": True}


def test_register_and_account(client):
    r = client.post("/auth/register", json={"email": "new@mail.test", "password": "long-enough-pw",
                                            "display_name": "New Person"})
    assert r.status_code == 201
    h = {"Authorization": "Bearer " + r.get_json()["token"]}
    assert client.get("/account", headers=h).get_json()["display_name"] == "New Person"
    r = client.patch("/account", headers=h, json={"display_name": "Renamed"})
    assert r.get_json()["display_name"] == "Renamed"


def test_login_rejects_bad_password(client):
    r = client.post("/auth/login", json={"email": "priya.shah@mail.test", "password": "nope"})
    assert r.status_code == 401


def test_list_own_orders(client, priya):
    orders = client.get("/orders", headers=priya).get_json()
    assert [o["status"] for o in orders] == ["processing", "delivered"]


def test_cancel_items_refunds(client, priya):
    r = client.post("/orders/2/cancel-items", headers=priya, json={"items": [{"sku": "TOWEL-LIN", "qty": 1}]})
    o = r.get_json()
    assert o["items"][0]["cancelled_qty"] == 1
    assert o["refunds"][0]["amount_pence"] == 800


def test_return_within_30_days(client, priya):
    r = client.post("/orders/1/returns", headers=priya, json={"items": [{"sku": "MUG-SPECK", "qty": 2}]})
    assert r.status_code == 200
    assert r.get_json()["refunds"][0]["amount_pence"] == 2400
    r = client.post("/orders/1/returns", headers=priya, json={"items": [{"sku": "MUG-SPECK", "qty": 1}]})
    assert r.status_code == 400


def test_cannot_return_someone_elses_order(client, priya):
    r = client.post("/orders/3/returns", headers=priya, json={"items": [{"sku": "BLANKET-WOOL", "qty": 1}]})
    assert r.status_code == 404


def test_products_sorted_and_search(client):
    names = [p["name"] for p in client.get("/products?sort=price_pence").get_json()]
    assert names[0] == "Linen tea towel"
    assert [p["sku"] for p in client.get("/products/search?q=mug").get_json()] == ["MUG-SPECK"]


def test_product_page_and_review(client, priya):
    assert client.post("/products/1/reviews", headers=priya, json={"body": "Lovely mug", "rating": 5}).status_code == 201
    page = client.get("/p/MUG-SPECK")
    assert b"Lovely mug" in page.data and b"<li>350 ml</li>" in page.data
    assert client.get("/p/MUG-SPECK", headers={"If-None-Match": page.headers["ETag"]}).status_code == 304


def test_basket_checkout_and_giftcard(client):
    tom = login(client, "tom.okafor@mail.test")
    r = client.post("/basket/items", json={"sku": "CARAFE", "qty": 1})
    assert r.get_json()["total_pence"] == 2800
    r = client.post("/basket/checkout", headers=tom)
    order_id = r.get_json()["order_id"]
    r = client.post("/giftcards/redeem", headers=tom, json={"code": "hfdemo10", "order_id": order_id,
                                                            "amount_pence": 600})
    assert r.get_json() == {"code": "HFDEMO10", "balance_pence": 400, "order_total_pence": 2200}


def test_admin_requires_staff(client, priya, staff):
    assert client.get("/admin/users", headers=priya).status_code == 403
    assert client.get("/admin/users", headers=staff).status_code == 200
    r = client.post("/admin/refunds", headers=staff, json={"order_id": 3, "amount_pence": 500})
    assert r.get_json()["refunded_pence"] == 500
    r = client.post("/admin/refunds", headers=staff, json={"order_id": 3, "amount_pence": 5000})
    assert r.status_code == 400


def test_admin_audit(client, staff):
    client.post("/admin/users/role", headers=staff, json={"user_id": 2, "role": "staff"})
    assert client.get("/admin/audit", headers=staff).get_json()[0]["action"] == "set_role"


def test_password_reset(client, app, monkeypatch):
    codes = {}
    monkeypatch.setattr("shopapi.auth.send_reset_email", lambda addr, code: codes.setdefault(addr, code))
    client.post("/auth/reset/request", json={"email": "tom.okafor@mail.test"})
    r = client.post("/auth/reset/confirm", json={"email": "tom.okafor@mail.test", "code": codes["tom.okafor@mail.test"],
                                                 "password": "a-brand-new-pw"})
    assert r.status_code == 200
    login(client, "tom.okafor@mail.test", "a-brand-new-pw")


def test_webhook_marks_paid(client, app):
    tom = login(client, "tom.okafor@mail.test")
    client.post("/basket/items", json={"sku": "MUG-SPECK", "qty": 1})
    order_id = client.post("/basket/checkout", headers=tom).get_json()["order_id"]
    with app.app_context():
        from shopapi.payments import webhook_signature
        sig = webhook_signature(order_id)
    r = client.post("/webhooks/payments", headers={"X-Signature": sig},
                    json={"order_id": order_id, "status": "paid", "amount_pence": 1200})
    assert r.status_code == 200
    assert client.get(f"/orders/{order_id}", headers=tom).get_json()["status"] == "processing"
