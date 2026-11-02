"""Orders, cancellations and returns."""
import datetime as dt

from flask import Blueprint, abort, g, jsonify, request

from .auth import require_auth
from .db import get_db
from .payments import issue_refund

bp = Blueprint("orders", __name__)
RETURN_DAYS = 30


def order_json(order):
    db = get_db()
    items = db.execute("SELECT sku, qty, price_pence, cancelled_qty, returned_qty FROM order_items WHERE order_id = ?",
                       (order["id"],)).fetchall()
    refunds = db.execute("SELECT amount_pence, kind, created FROM refunds WHERE order_id = ? ORDER BY id",
                         (order["id"],)).fetchall()
    return {"id": order["id"], "status": order["status"], "total_pence": order["total_pence"],
            "paid_pence": order["paid_pence"], "delivered_on": order["delivered_on"], "created": order["created"],
            "items": [dict(i) for i in items], "refunds": [dict(r) for r in refunds]}


def get_order(order_id):
    order = get_db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        abort(404, "no such order")
    return order


def own_order(order_id):
    order = get_order(order_id)
    if order["customer_id"] != g.user["id"]:
        abort(404, "no such order")
    return order


@bp.get("/orders")
@require_auth
def list_orders():
    rows = get_db().execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (g.user["id"],)).fetchall()
    return jsonify([order_json(o) for o in rows])


@bp.get("/orders/<int:order_id>")
@require_auth
def show_order(order_id):
    return jsonify(order_json(get_order(order_id)))


@bp.post("/orders/<int:order_id>/cancel-items")
@require_auth
def cancel_items(order_id):
    """Cancel some items while the order is still processing; they're refunded straight away."""
    order = own_order(order_id)
    if order["status"] != "processing":
        abort(400, "only orders that haven't been dispatched can be changed")
    db = get_db()
    total = 0
    for line in request.get_json(force=True).get("items", []):
        item = db.execute("SELECT * FROM order_items WHERE order_id = ? AND sku = ?",
                          (order_id, line.get("sku"))).fetchone()
        qty = int(line.get("qty", 0))
        if item is None or qty < 1 or item["cancelled_qty"] + qty > item["qty"]:
            abort(400, f"can't cancel {qty} of {line.get('sku')}")
        db.execute("UPDATE order_items SET cancelled_qty = cancelled_qty + ? WHERE id = ?", (qty, item["id"]))
        total += qty * item["price_pence"]
    if total:
        issue_refund(order, total, "cancellation")
    db.commit()
    return jsonify(order_json(get_order(order_id)))


@bp.post("/orders/<int:order_id>/returns")
@require_auth
def return_items(order_id):
    """Return delivered items within 30 days; the refund goes out as soon as the return is booked."""
    order = own_order(order_id)
    if order["status"] != "delivered":
        abort(400, "only delivered orders can be returned")
    delivered = dt.date.fromisoformat(order["delivered_on"])
    if (dt.date.today() - delivered).days > RETURN_DAYS:
        abort(400, "the 30-day return period has passed")
    db = get_db()
    total = 0
    for line in request.get_json(force=True).get("items", []):
        item = db.execute("SELECT * FROM order_items WHERE order_id = ? AND sku = ?",
                          (order_id, line.get("sku"))).fetchone()
        qty = int(line.get("qty", 0))
        if item is None or qty < 1 or item["returned_qty"] + qty > item["qty"]:
            abort(400, f"can't return {qty} of {line.get('sku')}")
        db.execute("UPDATE order_items SET returned_qty = returned_qty + ? WHERE id = ?", (qty, item["id"]))
        total += qty * item["price_pence"]
    if total:
        issue_refund(order, total, "return")
    db.commit()
    return jsonify(order_json(get_order(order_id)))
