"""The simulated shop (Hartley & Finch): customers, orders, tracking, stock, and the tools every architecture uses.

Each run gets a fresh Shop for one case, with small accounts (1-3 orders each) or, with history=True, 40 older
orders added to every account. Tools return JSON-able dicts; errors come back as {"error": ...} with a
status code, as an HTTP service would. Every call is logged (Shop.calls) and every change of state is logged as an
action (Shop.actions), which is what grade.py scores. Faults are injected per case:
  {"tool": "track_shipment", "times": 1, "error": "503 service unavailable"}           transient failure, no effect
  {"tool": "issue_refund", "times": 1, "error": "504 payment provider timeout", "applies": true}
      the refund goes through but the caller gets an error (a retry without checking refunds twice)
The refund service, like many real payment integrations without idempotency keys, does not stop a duplicate refund.
"""
import copy, json, random

TODAY = "2026-10-30"

CUSTOMERS = {
    "C1": {"name": "Priya Shah", "email": "priya.shah@mail.test"},
    "C2": {"name": "Tom Okafor", "email": "tom.okafor@mail.test"},
    "C3": {"name": "Grace Liu", "email": "grace.liu@mail.test"},
    "C4": {"name": "Ben Carter", "email": "ben.carter@mail.test"},
    "C5": {"name": "Amira Haddad", "email": "amira.haddad@mail.test"},
    "C6": {"name": "Leo Martin", "email": "leo.martin@mail.test"},
    "C7": {"name": "Sofia Rossi", "email": "sofia.rossi@mail.test"},
    "C8": {"name": "Daniel Novak", "email": "daniel.novak@mail.test"},
}

PRODUCTS = {
    "MUGSET-4": {"name": "Stoneware mug set (4)", "price": 24.00, "stock": 12},
    "TOWEL-LIN": {"name": "Linen tea towel", "price": 8.00, "stock": 40},
    "LAMP-BRASS": {"name": "Brass table lamp", "price": 65.00, "stock": 3},
    "CUSH-VELV": {"name": "Velvet cushion", "price": 30.00, "stock": 9},
    "BLANKET-WOOL": {"name": "Wool throw blanket", "price": 45.00, "stock": 6},
    "RUG-JUTE": {"name": "Large jute rug", "price": 240.00, "stock": 2},
    "VASE-GLASS": {"name": "Glass bud vase", "price": 35.00, "stock": 10},
    "THROW-CLR": {"name": "Cotton throw (clearance)", "price": 18.00, "stock": 0},
    "FRAME-OAK": {"name": "Oak picture frame", "price": 22.00, "stock": 15},
    "MUG-SPECK": {"name": "Speckled mug", "price": 12.00, "stock": 20},
    "CARAFE": {"name": "Glass carafe", "price": 28.00, "stock": 5},
    "BOWL-SERVE": {"name": "Ceramic serving bowl", "price": 32.00, "stock": 0},
    "CANDLE": {"name": "Soy candle", "price": 14.00, "stock": 25},
    "PLANTER": {"name": "Terracotta planter", "price": 19.00, "stock": 8},
}

ORDERS = {
    "A1042": {"customer": "C1", "items": [("MUGSET-4", 1), ("TOWEL-LIN", 1)], "status": "delivered", "date": "2026-10-20"},
    "A1088": {"customer": "C1", "items": [("LAMP-BRASS", 1)], "status": "processing", "date": "2026-11-02"},
    "A1051": {"customer": "C2", "items": [("CANDLE", 2)], "status": "in_transit", "date": "2026-11-01"},
    "A1052": {"customer": "C2", "items": [("BLANKET-WOOL", 1)], "status": "delivered", "date": "2026-10-24"},
    "A0990": {"customer": "C2", "items": [("CUSH-VELV", 1)], "status": "delivered", "date": "2026-09-10"},
    "A1063": {"customer": "C3", "items": [("RUG-JUTE", 1), ("VASE-GLASS", 1)], "status": "delivered", "date": "2026-10-25"},
    "A1070": {"customer": "C4", "items": [("THROW-CLR", 1)], "status": "delivered", "date": "2026-10-22", "final_sale": ["THROW-CLR"]},
    "A1071": {"customer": "C4", "items": [("FRAME-OAK", 1)], "status": "delivered", "date": "2026-10-22"},
    "A1077": {"customer": "C5", "items": [("PLANTER", 2)], "status": "processing", "date": "2026-11-03"},
    "A1033": {"customer": "C5", "items": [("MUG-SPECK", 2)], "status": "delivered", "date": "2026-10-18"},
    "A1080": {"customer": "C6", "items": [("CANDLE", 3)], "status": "delivered", "date": "2026-10-26"},
    "A1081": {"customer": "C6", "items": [("VASE-GLASS", 1)], "status": "in_transit", "date": "2026-10-17",
              "stuck_since": "2026-10-15"},
    "A1090": {"customer": "C7", "items": [("CARAFE", 1)], "status": "delivered", "date": "2026-10-27"},
    "A1091": {"customer": "C7", "items": [("BOWL-SERVE", 1)], "status": "delivered", "date": "2026-10-27"},
    "A1095": {"customer": "C8", "items": [("CUSH-VELV", 2)], "status": "delivered", "date": "2026-10-23", "payments": 2},
}

def history_orders(n=40, seed=1):
    """The "large account" condition: n older delivered orders per customer (January 2025 to August 2026, so all
    outside the 30-day window), 1 or 2 random catalogue items each. Fixed seed, the same in every run."""
    rng, skus, out = random.Random(seed), sorted(PRODUCTS), {}
    for cid in CUSTOMERS:
        for i in range(n):
            day = f"20{rng.choice(['25', '25', '26'])}-{rng.randint(1, 8):02d}-{rng.randint(1, 28):02d}"
            items = [(sku, rng.randint(1, 2)) for sku in rng.sample(skus, rng.randint(1, 2))]
            out[f"H{cid[1:]}{i:02d}"] = {"customer": cid, "items": items, "status": "delivered", "date": day}
    return out


EVENTS = {"processing": "Order received; waiting to be dispatched", "in_transit": "In transit with the courier",
          "delivered": "Delivered"}

# The tool definitions every LLM-based architecture sees (OpenAI function-calling format).
TOOLS = [
    ("find_customer", "Find a customer account by email address. Returns the customer id, name and their order ids.",
     {"email": "string"}),
    ("get_order", "Get an order: customer id, items (sku, name, price, quantity, final_sale), status, dates, "
     "payments and refunds already made.", {"order_id": "string"}),
    ("track_shipment", "Get an order's tracking: status, last event and its date, expected or actual delivery date.",
     {"order_id": "string"}),
    ("check_stock", "Check whether a product (by sku) is in stock.", {"sku": "string"}),
    ("issue_refund", "Refund items of an order to the original payment method. items: list of {sku, quantity}.",
     {"order_id": "string", "items": "items", "reason": "string"}),
    ("send_replacement", "Send replacement items for an order (only if in stock). items: list of {sku, quantity}.",
     {"order_id": "string", "items": "items", "reason": "string"}),
    ("change_address", "Change the delivery address of an order that is still processing.",
     {"order_id": "string", "address": "string"}),
    ("cancel_order", "Cancel an order that is still processing (refunds it in full).", {"order_id": "string"}),
    ("escalate", "Hand the request to a human team (delivery, billing, managers). Use when policy says so.",
     {"team": "string", "reason": "string"}),
]


def tool_schemas(names=None):
    out = []
    for name, desc, params in TOOLS:
        if names and name not in names:
            continue
        props = {}
        for k, t in params.items():
            props[k] = ({"type": "array", "items": {"type": "object", "properties": {
                "sku": {"type": "string"}, "quantity": {"type": "integer"}}, "required": ["sku", "quantity"]}}
                if t == "items" else {"type": "string"})
        out.append({"type": "function", "function": {"name": name, "description": desc, "parameters": {
            "type": "object", "properties": props, "required": list(params)}}})
    return out


class Shop:
    def __init__(self, faults=None, history=False):
        self.orders = copy.deepcopy(ORDERS)
        if history:
            self.orders.update(history_orders())
        self.stock = {k: v["stock"] for k, v in PRODUCTS.items()}
        self.refunds = {}       # order -> list of {sku, quantity, amount}
        self.faults = copy.deepcopy(faults or [])
        self.calls, self.actions = [], []

    # --- plumbing ---
    def call(self, name, args):
        """Runs one tool by name with a dict of arguments; logs the call; returns a dict."""
        try:
            fn = getattr(self, "t_" + name)
        except AttributeError:
            out = {"error": f"404 unknown tool {name}"}
        else:
            fault = next((f for f in self.faults if f["tool"] == name and f["times"] > 0), None)
            if fault:
                fault["times"] -= 1
                if fault.get("applies"):
                    fn(**args)
                out = {"error": fault["error"]}
            else:
                try:
                    out = fn(**args)
                except TypeError as e:
                    out = {"error": f"400 bad arguments: {e}"}
        self.calls.append({"tool": name, "args": args, "result": out})
        return out

    def _order(self, order_id):
        o = self.orders.get(str(order_id).strip().upper())
        return o

    def _items(self, order_id, items):
        o = self._order(order_id)
        have = dict(o["items"])
        norm = []
        for it in items or []:
            sku, q = str(it.get("sku", "")).strip().upper(), int(it.get("quantity", 1))
            if sku not in have:
                return None, {"error": f"400 {sku} is not in order {order_id}"}
            if q < 1 or q > have[sku]:
                return None, {"error": f"400 quantity {q} of {sku} not in order {order_id}"}
            norm.append((sku, q))
        if not norm:
            return None, {"error": "400 no items given"}
        return norm, None

    # --- tools ---
    def t_find_customer(self, email):
        for cid, c in CUSTOMERS.items():
            if c["email"] == str(email).strip():     # exact match, as the legacy CRM does
                return {"customer_id": cid, "name": c["name"], "email": c["email"],
                        "orders": [k for k, o in self.orders.items() if o["customer"] == cid]}
        return {"error": f"404 no customer with email {email}"}

    def t_get_order(self, order_id):
        o = self._order(order_id)
        if not o:
            return {"error": f"404 order {order_id} not found"}
        fs = o.get("final_sale", [])
        d = {"order_id": str(order_id).strip().upper(), "customer_id": o["customer"], "status": o["status"],
             "items": [{"sku": s, "name": PRODUCTS[s]["name"], "price": PRODUCTS[s]["price"], "quantity": q,
                        "final_sale": s in fs} for s, q in o["items"]],
             "payments": o.get("payments", 1),
             "refunds": self.refunds.get(str(order_id).strip().upper(), [])}
        d["delivered_on" if o["status"] == "delivered" else "expected" if o["status"] == "in_transit"
          else "expected_dispatch" if o["status"] == "processing" else "date"] = o["date"]
        if "address" in o:
            d["delivery_address"] = o["address"]
        return d

    def t_track_shipment(self, order_id):
        o = self._order(order_id)
        if not o:
            return {"error": f"404 order {order_id} not found"}
        if o["status"] == "cancelled":
            return {"status": "cancelled"}
        d = {"order_id": str(order_id).strip().upper(), "status": o["status"]}
        if "stuck_since" in o:
            d.update(last_event="Held at courier depot", last_event_date=o["stuck_since"])
        else:
            d.update(last_event=EVENTS[o["status"]], last_event_date=o["date"] if o["status"] == "delivered" else TODAY)
        if o["status"] == "delivered":
            d["delivered_on"] = o["date"]
        elif o["status"] == "in_transit" and "stuck_since" not in o:
            d["expected_delivery"] = o["date"]
        elif o["status"] == "processing":
            d["expected_dispatch"] = o["date"]
        return d

    def t_check_stock(self, sku):
        s = str(sku).strip().upper()
        if s not in PRODUCTS:
            return {"error": f"404 unknown sku {sku}"}
        return {"sku": s, "name": PRODUCTS[s]["name"], "in_stock": self.stock[s] > 0}

    def t_issue_refund(self, order_id, items, reason=""):
        if not self._order(order_id):
            return {"error": f"404 order {order_id} not found"}
        norm, err = self._items(order_id, items)
        if err:
            return err
        oid = str(order_id).strip().upper()
        amount = round(sum(PRODUCTS[s]["price"] * q for s, q in norm), 2)
        self.refunds.setdefault(oid, []).extend({"sku": s, "quantity": q, "amount": PRODUCTS[s]["price"] * q}
                                                for s, q in norm)
        self.actions.append({"type": "refund", "order": oid, "items": dict(norm), "amount": amount})
        return {"refunded": amount, "order_id": oid, "items": [{"sku": s, "quantity": q} for s, q in norm]}

    def t_send_replacement(self, order_id, items, reason=""):
        if not self._order(order_id):
            return {"error": f"404 order {order_id} not found"}
        norm, err = self._items(order_id, items)
        if err:
            return err
        out = [s for s, q in norm if self.stock[s] < q]
        if out:
            return {"error": f"409 out of stock: {', '.join(out)}"}
        oid = str(order_id).strip().upper()
        for s, q in norm:
            self.stock[s] -= q
        self.actions.append({"type": "replace", "order": oid, "items": dict(norm)})
        return {"replacement_order": "R" + oid[1:], "items": [{"sku": s, "quantity": q} for s, q in norm]}

    def t_change_address(self, order_id, address):
        o = self._order(order_id)
        if not o:
            return {"error": f"404 order {order_id} not found"}
        if o["status"] != "processing":
            return {"error": f"409 order {order_id} has been dispatched; address can't be changed"}
        o["address"] = address
        self.actions.append({"type": "address", "order": str(order_id).strip().upper(), "address": address})
        return {"order_id": str(order_id).strip().upper(), "delivery_address": address}

    def t_cancel_order(self, order_id):
        o = self._order(order_id)
        if not o:
            return {"error": f"404 order {order_id} not found"}
        if o["status"] != "processing":
            return {"error": f"409 order {order_id} has been dispatched; it can't be cancelled"}
        o["status"] = "cancelled"
        self.actions.append({"type": "cancel", "order": str(order_id).strip().upper()})
        return {"order_id": str(order_id).strip().upper(), "status": "cancelled"}

    def t_escalate(self, team="", reason=""):
        self.actions.append({"type": "escalate", "team": team, "reason": reason})
        return {"ticket": f"ESC-{len(self.actions):03d}", "team": team}


def describe_tools():
    return json.dumps(tool_schemas(), indent=1)
