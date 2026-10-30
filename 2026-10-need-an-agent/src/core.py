"""The fixed control flow shared by the two "code decides" architectures: plain code (rules.py) and the workflow
(workflow.py). Written from the requirements in README.md ("What the workflow was built for"), before any run.

Four intents are handled; anything else is escalated with a holding reply:
  delivery_status (where is it / never arrived / tracking stuck), return_refund, damaged_item, policy_question.
The policy's rules (30 days, final sale, £200, stock, sender check, 2 and 7 days for deliveries) are checked here, in
code. Error handling, as a careful developer would build it: reads are retried up to twice on 5xx errors; an order
number that isn't found is looked up among the customer's own orders by the items mentioned; writes (refunds,
replacements) are never retried: a failed write is escalated, so money can't be sent twice.
What differs between the two architectures is the language work, passed in as a strategy object `s`:
  s.understand(email) -> {intent, order_id, items: [{"name", "quantity"}], preference, problem}
  s.answer_question(email) -> reply text;  s.write_reply(email, facts) -> reply text
"""
from datetime import date

from shop import PRODUCTS, TODAY

STOP = {"set", "large", "glass", "the", "of", "a", "(4)", "(clearance)", "cotton"}


def days_since(iso):
    return (date.fromisoformat(TODAY) - date.fromisoformat(iso)).days


def read(shop, tool, **args):
    """A read with up to two retries on 5xx errors."""
    for _ in range(3):
        out = shop.call(tool, args)
        if not str(out.get("error", "")).startswith("5"):
            return out
    return out


def match_items(mentions, order_items, text=""):
    """Order lines that the mentioned item names (or the email text) refer to: [(sku, quantity)]."""
    words = " ".join([m.get("name") or "" for m in mentions] + [text]).lower()
    found = []
    for it in order_items:
        keys = [w for w in it["name"].lower().split() if w not in STOP and len(w) > 2]
        if any(k in words for k in keys):
            q = next((m.get("quantity") for m in mentions if m.get("name") and any(k in m["name"].lower() for k in keys)),
                     None)
            found.append((it["sku"], min(int(q), it["quantity"]) if q else it["quantity"]))
    return found


def handle(email, shop, s):
    u = s.understand(email)
    intent = u.get("intent")
    if intent == "policy_question":
        return s.answer_question(email)
    if intent not in ("delivery_status", "return_refund", "damaged_item"):
        shop.call("escalate", {"team": "support", "reason": "request type not handled automatically"})
        return s.write_reply(email, {"outcome": "escalated", "team": "customer service"})

    cust = read(shop, "find_customer", email=email["sender"])
    if "error" in cust:
        return s.write_reply(email, {"outcome": "sender_not_recognised",
                                     "ask": "write from the email address on your account"})

    order = None
    if u.get("order_id"):
        order = read(shop, "get_order", order_id=u["order_id"])
        if "error" in order:
            order = None
    if order is None:   # no number, or not found: look among this customer's orders for the items mentioned
        hits = []
        for oid in cust["orders"]:
            o = read(shop, "get_order", order_id=oid)
            if "error" not in o and match_items(u.get("items") or [], o["items"], email["body"]):
                hits.append(o)
        if len(hits) != 1:
            return s.write_reply(email, {"outcome": "need_order_number"})
        order = hits[0]
    if order["customer_id"] != cust["customer_id"]:
        return s.write_reply(email, {"outcome": "not_your_order", "ask": "write from the email address on the account"})
    oid = order["order_id"]

    if intent == "delivery_status":
        t = read(shop, "track_shipment", order_id=oid)
        if "error" in t:
            shop.call("escalate", {"team": "delivery", "reason": f"tracking unavailable for {oid}"})
            return s.write_reply(email, {"outcome": "escalated", "team": "delivery"})
        problem = u.get("problem")
        if problem == "not_received" and t["status"] == "delivered" and days_since(t["delivered_on"]) > 2:
            shop.call("escalate", {"team": "delivery", "reason": f"{oid} shows delivered but not received"})
            return s.write_reply(email, {"outcome": "escalated", "team": "delivery", "order": oid})
        if t["status"] == "in_transit" and days_since(t["last_event_date"]) > 7:
            items = [(i["sku"], i["quantity"]) for i in order["items"]]
            return replace_or_refund(email, shop, s, order, items, u.get("preference"), "lost in transit")
        return s.write_reply(email, {"outcome": "tracking", "order": oid, **{k: v for k, v in t.items() if k != "order_id"}})

    items = match_items(u.get("items") or [], order["items"], email["body"])
    if not items and len(order["items"]) == 1:
        items = [(order["items"][0]["sku"], order["items"][0]["quantity"])]
    if not items:
        return s.write_reply(email, {"outcome": "need_item", "order": oid})
    if order["status"] != "delivered":
        return s.write_reply(email, {"outcome": "not_delivered_yet", "order": oid, "status": order["status"]})
    if days_since(order["delivered_on"]) > 30:
        return s.write_reply(email, {"outcome": "declined", "reason": "more than 30 days since delivery",
                                     "delivered_on": order["delivered_on"]})
    final = {i["sku"] for i in order["items"] if i["final_sale"]}
    if intent == "return_refund" and any(sku in final for sku, _ in items):
        return s.write_reply(email, {"outcome": "declined", "reason": "final-sale (clearance) item, not faulty"})
    if intent == "damaged_item":
        return replace_or_refund(email, shop, s, order, items, u.get("preference"), "damaged on arrival")
    return refund(email, shop, s, order, items, "return within 30 days")


def refund(email, shop, s, order, items, reason, note=None):
    amount = round(sum(PRODUCTS[sku]["price"] * q for sku, q in items), 2)
    if amount > 200:
        shop.call("escalate", {"team": "managers", "reason": f"refund of £{amount} on {order['order_id']} needs approval"})
        return s.write_reply(email, {"outcome": "escalated", "team": "a manager (refunds over £200 need approval)"})
    r = shop.call("issue_refund", {"order_id": order["order_id"], "items": [{"sku": k, "quantity": q} for k, q in items],
                                   "reason": reason})
    if "error" in r:
        shop.call("escalate", {"team": "support", "reason": f"refund failed: {r['error']}"})
        return s.write_reply(email, {"outcome": "escalated", "team": "customer service"})
    facts = {"outcome": "refunded", "amount": r["refunded"], "items": [PRODUCTS[k]["name"] for k, _ in items],
             "timing": "back to the original payment method within 5 working days"}
    if note:
        facts["note"] = note
    return s.write_reply(email, facts)


def replace_or_refund(email, shop, s, order, items, preference, reason):
    if preference == "refund":
        return refund(email, shop, s, order, items, reason)
    in_stock = all(read(shop, "check_stock", sku=sku).get("in_stock") for sku, _ in items)
    if not in_stock:
        return refund(email, shop, s, order, items, reason, note="the item is out of stock, so it has been refunded")
    r = shop.call("send_replacement", {"order_id": order["order_id"],
                                       "items": [{"sku": k, "quantity": q} for k, q in items], "reason": reason})
    if "error" in r:
        shop.call("escalate", {"team": "support", "reason": f"replacement failed: {r['error']}"})
        return s.write_reply(email, {"outcome": "escalated", "team": "customer service"})
    return s.write_reply(email, {"outcome": "replacement_sent", "items": [PRODUCTS[k]["name"] for k, _ in items],
                                 "replacement_order": r["replacement_order"]})
