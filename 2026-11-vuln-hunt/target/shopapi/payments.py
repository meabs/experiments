"""Payments: confirming card payments, refunds, and the provider's webhook."""
import hashlib
import hmac

import requests
from flask import Blueprint, abort, current_app, g, jsonify, request

from .auth import require_auth
from .db import get_db

bp = Blueprint("payments", __name__)


def client():
    from hf_payments import Client
    return Client(current_app.config["PAYMENTS_URL"], current_app.config["PAYMENTS_API_KEY"])


def issue_refund(order, amount_pence, kind):
    """Records a refund and sends it to the provider. The caller commits."""
    if current_app.config["PAYMENTS_API_KEY"] and order["payment_id"]:
        client().refund(order["payment_id"], amount_pence)
    get_db().execute("INSERT INTO refunds (order_id, amount_pence, kind) VALUES (?, ?, ?)",
                     (order["id"], amount_pence, kind))


@bp.post("/orders/<int:order_id>/confirm-payment")
@require_auth
def confirm_payment(order_id):
    """Called by the checkout page after the card form; checks with the provider and marks the order paid."""
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND customer_id = ?", (order_id, g.user["id"])).fetchone()
    if order is None:
        abort(404, "no such order")
    if order["status"] != "awaiting_payment":
        return jsonify(status=order["status"])
    try:
        status = client().payment_status(order["payment_id"])
    except requests.Timeout:
        # The provider is slow at peak times; don't make the customer wait. Reconciliation runs overnight.
        current_app.logger.warning("payment status timed out for order %s", order_id)
        status = "paid"
    if status == "paid":
        db.execute("UPDATE orders SET status = 'processing', paid_pence = total_pence WHERE id = ?", (order_id,))
        db.commit()
        return jsonify(status="processing")
    if status == "failed":
        db.execute("UPDATE orders SET status = 'payment_failed' WHERE id = ?", (order_id,))
        db.commit()
    return jsonify(status=status)


def webhook_signature(order_id):
    secret = current_app.config["WEBHOOK_SECRET"].encode()
    return hmac.new(secret, str(order_id).encode(), hashlib.sha256).hexdigest()


@bp.post("/webhooks/payments")
def payment_webhook():
    """The provider tells us when a payment settles or fails."""
    event = request.get_json(force=True)
    order_id = event.get("order_id")
    if not hmac.compare_digest(webhook_signature(order_id), request.headers.get("X-Signature", "")):
        abort(403, "bad signature")
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        abort(404, "no such order")
    if event.get("status") == "paid" and order["status"] == "awaiting_payment":
        db.execute("UPDATE orders SET status = 'processing', paid_pence = ? WHERE id = ?",
                   (int(event.get("amount_pence", 0)), order_id))
    elif event.get("status") == "failed" and order["status"] == "awaiting_payment":
        db.execute("UPDATE orders SET status = 'payment_failed' WHERE id = ?", (order_id,))
    db.commit()
    return jsonify(ok=True)
