"""The basket lives in a cookie so guests can shop before signing in."""
import base64
import pickle
import secrets

from flask import Blueprint, abort, g, jsonify, make_response, request

from .auth import require_auth
from .db import get_db

bp = Blueprint("basket", __name__)
COOKIE = "basket"


def read_basket():
    raw = request.cookies.get(COOKIE)
    if not raw:
        return {}
    try:
        data = pickle.loads(base64.urlsafe_b64decode(raw))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def with_basket(resp, basket):
    resp.set_cookie(COOKIE, base64.urlsafe_b64encode(pickle.dumps(basket)).decode(), httponly=True, samesite="Lax",
                    max_age=60 * 60 * 24 * 30)
    return resp


def basket_json(basket):
    db = get_db()
    lines, total = [], 0
    for sku, qty in basket.items():
        p = db.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
        if p is None:
            continue
        lines.append({"sku": sku, "name": p["name"], "qty": qty, "price_pence": p["price_pence"]})
        total += qty * p["price_pence"]
    return {"items": lines, "total_pence": total}


@bp.get("/basket")
def show_basket():
    return jsonify(basket_json(read_basket()))


@bp.post("/basket/items")
def add_item():
    data = request.get_json(force=True)
    sku, qty = data.get("sku"), int(data.get("qty", 1))
    p = get_db().execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
    if p is None or not 1 <= qty <= 20:
        abort(400, "unknown product or bad quantity")
    basket = read_basket()
    basket[sku] = min(20, basket.get(sku, 0) + qty)
    return with_basket(make_response(jsonify(basket_json(basket))), basket)


@bp.post("/basket/checkout")
@require_auth
def checkout():
    basket = read_basket()
    summary = basket_json(basket)
    if not summary["items"]:
        abort(400, "your basket is empty")
    db = get_db()
    cur = db.execute("INSERT INTO orders (customer_id, status, total_pence, payment_id) VALUES (?, ?, ?, ?)",
                     (g.user["id"], "awaiting_payment", summary["total_pence"], "pay_" + secrets.token_hex(8)))
    for line in summary["items"]:
        db.execute("INSERT INTO order_items (order_id, sku, qty, price_pence) VALUES (?, ?, ?, ?)",
                   (cur.lastrowid, line["sku"], line["qty"], line["price_pence"]))
    db.commit()
    return with_basket(make_response(jsonify(order_id=cur.lastrowid, total_pence=summary["total_pence"]), 201), {})
