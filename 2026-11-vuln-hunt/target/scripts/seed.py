"""Creates shop.db with demo data. Usage: python scripts/seed.py"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopapi import create_app  # noqa: E402
from shopapi.auth import hash_password  # noqa: E402
from shopapi.db import get_db, init_db  # noqa: E402

PRODUCTS = [
    ("MUG-SPECK", "Speckled mug", 1200, "Hand-glazed stoneware.\n\n- 350 ml\n- Dishwasher safe", 40),
    ("TOWEL-LIN", "Linen tea towel", 800, "Stonewashed **linen**.", 120),
    ("VASE-GLASS", "Glass bud vase", 3500, "Mouth-blown glass.", 12),
    ("RUG-JUTE", "Large jute rug", 24000, "Natural jute, 160 × 230 cm.", 3),
    ("BLANKET-WOOL", "Wool throw blanket", 4500, "Lambswool, woven in Wales.", 18),
    ("CARAFE", "Glass carafe", 2800, "1 litre.", 25),
]
USERS = [("priya.shah@mail.test", "Priya Shah", "customer"), ("tom.okafor@mail.test", "Tom Okafor", "customer"),
         ("admin@hartleyfinch.co.uk", "Support", "staff")]


def seed(app):
    with app.app_context():
        db = get_db()
        init_db()
        for sku, name, price, desc, stock in PRODUCTS:
            db.execute("INSERT OR IGNORE INTO products (sku, name, price_pence, description_md, stock) "
                       "VALUES (?, ?, ?, ?, ?)", (sku, name, price, desc, stock))
        for email, name, role in USERS:
            db.execute("INSERT OR IGNORE INTO users (email, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
                       (email, hash_password("demo-password-1"), name, role))
        today = dt.date.today()
        orders = [(1, "delivered", [("MUG-SPECK", 2, 1200)], (today - dt.timedelta(days=5)).isoformat()),
                  (1, "processing", [("TOWEL-LIN", 3, 800)], None),
                  (2, "delivered", [("BLANKET-WOOL", 1, 4500)], (today - dt.timedelta(days=9)).isoformat())]
        if db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            for cust, status, items, delivered in orders:
                total = sum(q * p for _, q, p in items)
                cur = db.execute("INSERT INTO orders (customer_id, status, total_pence, paid_pence, payment_id, "
                                 "delivered_on) VALUES (?, ?, ?, ?, ?, ?)",
                                 (cust, status, total, total, f"pay_demo{cust}{status[:3]}", delivered))
                for sku, q, p in items:
                    db.execute("INSERT INTO order_items (order_id, sku, qty, price_pence) VALUES (?, ?, ?, ?)",
                               (cur.lastrowid, sku, q, p))
            db.execute("INSERT INTO giftcards (code, balance_pence, owner_id) VALUES ('HFDEMO10', 1000, 2)")
        db.commit()


if __name__ == "__main__":
    seed(create_app())
    print("seeded", create_app().config["DATABASE"])
