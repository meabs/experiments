"""Gift cards: redeem part or all of a card's balance against an unpaid order."""
from flask import Blueprint, abort, g, jsonify, request

from .auth import require_auth
from .db import get_db

bp = Blueprint("giftcards", __name__)


@bp.get("/giftcards/<code>")
@require_auth
def balance(code):
    card = get_db().execute("SELECT * FROM giftcards WHERE code = ?", (code.upper(),)).fetchone()
    if card is None:
        abort(404, "no such gift card")
    return jsonify(code=card["code"], balance_pence=card["balance_pence"])


def record_redemption(db, code, order_id, amount):
    db.execute("INSERT INTO giftcard_redemptions (code, order_id, amount_pence) VALUES (?, ?, ?)",
               (code, order_id, amount))
    db.execute("UPDATE orders SET total_pence = total_pence - ? WHERE id = ?", (amount, order_id))


@bp.post("/giftcards/redeem")
@require_auth
def redeem():
    data = request.get_json(force=True)
    code = (data.get("code") or "").upper()
    amount = int(data.get("amount_pence", 0))
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND customer_id = ?",
                       (data.get("order_id"), g.user["id"])).fetchone()
    if order is None or order["status"] != "awaiting_payment":
        abort(400, "gift cards can only be used on an unpaid order")
    card = db.execute("SELECT * FROM giftcards WHERE code = ?", (code,)).fetchone()
    if card is None:
        abort(404, "no such gift card")
    if amount < 1 or amount > card["balance_pence"] or amount > order["total_pence"]:
        abort(400, "amount must be between 1p and the card's balance and the order total")
    new_balance = card["balance_pence"] - amount
    record_redemption(db, code, order["id"], amount)
    db.execute("UPDATE giftcards SET balance_pence = ? WHERE code = ?", (new_balance, code))
    db.commit()
    return jsonify(code=code, balance_pence=new_balance, order_total_pence=order["total_pence"] - amount)
