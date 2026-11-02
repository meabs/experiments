"""Customer-service admin area. Access is checked for every admin route in create_app's before_request hook."""
import json
import secrets

from flask import Blueprint, abort, g, jsonify, request

from .db import get_db
from .payments import issue_refund

bp = Blueprint("admin", __name__, url_prefix="/admin")


def audit(action, detail):
    get_db().execute("INSERT INTO audit (actor_id, action, detail) VALUES (?, ?, ?)",
                     (g.user["id"], action, json.dumps(detail)))


@bp.get("/users")
def users():
    rows = get_db().execute("SELECT id, email, display_name, role, created FROM users ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/users/role")
def set_role():
    data = request.get_json(force=True)
    if data.get("role") not in ("customer", "staff"):
        abort(400, "role must be customer or staff")
    db = get_db()
    db.execute("UPDATE users SET role = ? WHERE id = ?", (data["role"], data.get("user_id")))
    audit("set_role", {"user_id": data.get("user_id"), "role": data["role"]})
    db.commit()
    return jsonify(ok=True)


@bp.post("/giftcards")
def issue_giftcard():
    data = request.get_json(force=True)
    amount = int(data.get("amount_pence", 0))
    if not 100 <= amount <= 50000:
        abort(400, "gift cards are £1 to £500")
    code = "HF" + secrets.token_hex(5).upper()
    db = get_db()
    db.execute("INSERT INTO giftcards (code, balance_pence, owner_id) VALUES (?, ?, ?)",
               (code, amount, data.get("owner_id")))
    audit("issue_giftcard", {"code": code, "amount_pence": amount, "owner_id": data.get("owner_id")})
    db.commit()
    return jsonify(code=code, balance_pence=amount), 201


# strict_slashes=False: the old support dashboard posts to /admin/refunds/
@bp.post("/refunds", strict_slashes=False)
def goodwill_refund():
    """A goodwill refund agreed by customer service, up to the amount paid."""
    data = request.get_json(force=True)
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (data.get("order_id"),)).fetchone()
    if order is None:
        abort(404, "no such order")
    amount = int(data.get("amount_pence", 0))
    refunded = db.execute("SELECT COALESCE(SUM(amount_pence), 0) FROM refunds WHERE order_id = ?",
                          (order["id"],)).fetchone()[0]
    if amount < 1 or refunded + amount > order["paid_pence"]:
        abort(400, "refund would exceed the amount paid")
    issue_refund(order, amount, "goodwill")
    db.commit()
    return jsonify(ok=True, refunded_pence=refunded + amount)


@bp.get("/reports/reviews")
def reviews_by_customer():
    """All reviews written under a customer's current display name (for moderation)."""
    db = get_db()
    customer = db.execute("SELECT * FROM users WHERE id = ?", (request.args.get("customer_id"),)).fetchone()
    if customer is None:
        abort(404, "no such customer")
    rows = db.execute(
        "SELECT r.id, p.name AS product, r.rating, r.body, r.created FROM reviews r "
        "JOIN products p ON p.id = r.product_id "
        f"WHERE r.author_name = '{customer['display_name']}' ORDER BY r.id DESC"
    ).fetchall()
    return jsonify(customer=customer["email"], reviews=[dict(r) for r in rows])


@bp.get("/audit")
def audit_log():
    rows = get_db().execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200").fetchall()
    return jsonify([dict(r) for r in rows])
