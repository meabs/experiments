"""Architecture 1, typed schema + state machine: the "boring" deterministic version, built to cover every kind of
request the policy describes (not just four, as need-an-agent's workflow did).

  1. understand: one model call turns the email into a typed list of requests (JSON, checked against the schema);
  2. plain code handles each request in turn: lookups, the policy's rules as if/else, and any action;
  3. write_reply: one model call writes a single reply from the facts the code decided (and the policy, when there
     is a policy question).
So 2 model calls per email, never a loop. Error handling is need-an-agent's core.py's: reads retried twice on 5xx,
writes never retried (a failed write is escalated, so money can't go twice), an order number that isn't found is
looked up among the customer's own orders by the items mentioned. Order numbers are normalised ("#a-1042" -> A1042).
Anything the schema can't express ("other") is escalated.
"""
import json, re

import base
from core import days_since, match_items, read      # need-an-agent's core.py: the same helpers as its workflow
from llm import parse_json
from shop import PRODUCTS, TODAY

POLICY = base.POLICY
INTENTS = {"delivery_status", "return_refund", "damaged_item", "policy_question", "change_address", "cancel_order",
           "hold_order", "billing_problem", "other"}

UNDERSTAND = """You read customer emails for Hartley & Finch, an online homeware shop. List every separate request in
the email. Return only a JSON object: {"requests": [ ... ]}, one entry per request, each:
{"intent": one of
   "delivery_status" (where is my order, it never arrived, tracking not moving),
   "return_refund" (wants to return an item or get a refund, item not damaged),
   "damaged_item" (item arrived damaged or faulty),
   "policy_question" (a general question about delivery, returns or payment, about no particular order),
   "change_address" (change an order's delivery address),
   "cancel_order" (cancel an order),
   "hold_order" (hold or delay an order's dispatch),
   "billing_problem" (charged twice, payment dispute or other billing problem),
   "other" (anything else),
 "order_id": the order number mentioned (e.g. "A1042") or null,
 "items": [{"name": item as the customer describes it, "quantity": number or null}],
 "preference": "refund", "replacement" or null (what they ask for, if they say),
 "problem": for delivery_status only: "where_is", "not_received" or "no_movement"; otherwise null,
 "new_address": for change_address only: the new address; otherwise null,
 "question": for policy_question only: the question in a few words; otherwise null}"""

REPLY = """You write replies to customers for Hartley & Finch, an online homeware shop. Write one short, friendly email
reply that answers every request. The facts below are what our system has decided and done, one entry per request:
state every fact that matters to the customer (amounts in £, dates, statuses, what happens next). Do not promise or
decide anything that is not in the facts. Sign off as Hartley & Finch."""


def norm_order(oid):
    s = re.sub(r"[^A-Za-z0-9]", "", str(oid or "")).upper()
    return s or None


def understand(email, llm):
    m = llm.chat([{"role": "system", "content": UNDERSTAND},
                  {"role": "user", "content": f"Subject: {email['subject']}\n\n{email['body']}"}], json_mode=True)
    d = parse_json(m.get("content")) or {}
    reqs = [r for r in d.get("requests") or [] if isinstance(r, dict)]
    for r in reqs:
        if r.get("intent") not in INTENTS:
            r["intent"] = "other"
        r["order_id"] = norm_order(r.get("order_id"))
        r["items"] = [i for i in (r.get("items") or []) if isinstance(i, dict)]
    return reqs or [{"intent": "other", "items": []}]


def write_reply(email, facts, llm, with_policy):
    system = REPLY + (f"\n\nAnswer any policy question from this policy only. Today is {TODAY}.\n\n{POLICY}"
                      if with_policy else "")
    m = llm.chat([{"role": "system", "content": system},
                  {"role": "user", "content": f"Customer's email:\nSubject: {email['subject']}\n\n{email['body']}"
                                              f"\n\nFacts (today is {TODAY}), one per request:\n{json.dumps(facts, indent=1)}"}])
    return m.get("content") or ""


def find_order(shop, cust, u):
    order = None
    if u.get("order_id"):
        order = read(shop, "get_order", order_id=u["order_id"])
        if "error" in order:
            order = None
    if order is None:   # no number, or not found: look among this customer's orders for the items mentioned
        hits = []
        for oid in cust["orders"]:
            o = read(shop, "get_order", order_id=oid)
            if "error" not in o and match_items(u["items"], o["items"]):
                hits.append(o)
        if len(hits) != 1:
            return None
        order = hits[0]
    return order


def refund(shop, order, items, reason, note=None):
    amount = round(sum(PRODUCTS[sku]["price"] * q for sku, q in items), 2)
    if amount > 200:
        shop.call("escalate", {"team": "managers", "reason": f"refund of £{amount} on {order['order_id']} needs approval"})
        return {"outcome": "escalated", "team": "a manager (refunds over £200 need approval)"}
    r = shop.call("issue_refund", {"order_id": order["order_id"], "items": [{"sku": k, "quantity": q} for k, q in items],
                                   "reason": reason})
    if "error" in r:
        shop.call("escalate", {"team": "support", "reason": f"refund failed: {r['error']}"})
        return {"outcome": "escalated", "team": "customer service"}
    f = {"outcome": "refunded", "order": order["order_id"], "amount": r["refunded"],
         "items": [PRODUCTS[k]["name"] for k, _ in items],
         "timing": "back to the original payment method within 5 working days"}
    if note:
        f["note"] = note
    return f


def replace_or_refund(shop, order, items, preference, reason):
    if preference == "refund":
        return refund(shop, order, items, reason)
    if not all(read(shop, "check_stock", sku=sku).get("in_stock") for sku, _ in items):
        return refund(shop, order, items, reason, note="the item is out of stock, so it has been refunded")
    r = shop.call("send_replacement", {"order_id": order["order_id"],
                                       "items": [{"sku": k, "quantity": q} for k, q in items], "reason": reason})
    if "error" in r:
        shop.call("escalate", {"team": "support", "reason": f"replacement failed: {r['error']}"})
        return {"outcome": "escalated", "team": "customer service"}
    return {"outcome": "replacement_sent", "order": order["order_id"], "items": [PRODUCTS[k]["name"] for k, _ in items],
            "replacement_order": r["replacement_order"]}


def handle(u, cust, shop):
    """One request -> the facts for the reply (and any action taken)."""
    intent = u["intent"]
    if intent == "policy_question":
        return {"request": "policy question", "question": u.get("question"), "answer": "from the policy"}
    if intent == "billing_problem":
        shop.call("escalate", {"team": "billing", "reason": f"billing problem on {u.get('order_id')}"})
        return {"request": "billing problem", "outcome": "escalated", "team": "billing"}
    if intent == "other":
        shop.call("escalate", {"team": "support", "reason": "request type not handled automatically"})
        return {"request": "other", "outcome": "escalated", "team": "customer service"}
    order = find_order(shop, cust, u)
    if order is None:
        return {"request": intent, "outcome": "need_order_number"}
    if order["customer_id"] != cust["customer_id"]:
        return {"request": intent, "outcome": "not_your_order", "ask": "write from the email address on the account"}
    oid = order["order_id"]

    if intent == "hold_order":
        return {"request": "hold order", "order": oid, "outcome": "cannot_hold",
                "offer": "we can cancel the order or change its address instead" if order["status"] == "processing"
                else "it has already been dispatched"}
    if intent in ("change_address", "cancel_order"):
        if order["status"] != "processing":
            return {"request": intent, "order": oid, "outcome": "declined", "reason": "already dispatched",
                    "status": order["status"]}
        if intent == "cancel_order":
            r = shop.call("cancel_order", {"order_id": oid})
            if "error" in r:
                shop.call("escalate", {"team": "support", "reason": f"cancel failed: {r['error']}"})
                return {"request": "cancel", "outcome": "escalated", "team": "customer service"}
            return {"request": "cancel", "order": oid, "outcome": "cancelled", "refund": "the whole order, back to the "
                    "original payment method within 5 working days"}
        if not u.get("new_address"):
            return {"request": "change address", "order": oid, "outcome": "need_new_address"}
        r = shop.call("change_address", {"order_id": oid, "address": u["new_address"]})
        if "error" in r:
            shop.call("escalate", {"team": "support", "reason": f"address change failed: {r['error']}"})
            return {"request": "change address", "outcome": "escalated", "team": "customer service"}
        return {"request": "change address", "order": oid, "outcome": "address_changed", "address": u["new_address"]}

    if intent == "delivery_status":
        t = read(shop, "track_shipment", order_id=oid)
        if "error" in t:
            shop.call("escalate", {"team": "delivery", "reason": f"tracking unavailable for {oid}"})
            return {"request": "delivery", "outcome": "escalated", "team": "delivery"}
        if u.get("problem") == "not_received" and t["status"] == "delivered" and days_since(t["delivered_on"]) > 2:
            shop.call("escalate", {"team": "delivery", "reason": f"{oid} shows delivered but not received"})
            return {"request": "delivery", "outcome": "escalated", "team": "delivery", "order": oid}
        if t["status"] == "in_transit" and days_since(t["last_event_date"]) > 7:
            items = [(i["sku"], i["quantity"]) for i in order["items"]]
            return {"request": "lost in transit",
                    **replace_or_refund(shop, order, items, u.get("preference"), "lost in transit")}
        return {"request": "delivery", "outcome": "tracking", "order": oid,
                **{k: v for k, v in t.items() if k != "order_id"}}

    items = match_items(u["items"], order["items"])
    if not items and len(order["items"]) == 1:
        items = [(order["items"][0]["sku"], order["items"][0]["quantity"])]
    if not items:
        return {"request": intent, "outcome": "need_item", "order": oid}
    if order["status"] != "delivered":
        return {"request": intent, "outcome": "not_delivered_yet", "order": oid, "status": order["status"]}
    if days_since(order["delivered_on"]) > 30:
        return {"request": intent, "order": oid, "outcome": "declined", "reason": "more than 30 days since delivery",
                "delivered_on": order["delivered_on"]}
    final = {i["sku"] for i in order["items"] if i["final_sale"]}
    if intent == "return_refund" and any(sku in final for sku, _ in items):
        return {"request": "return", "order": oid, "outcome": "declined", "reason": "final-sale (clearance) item, not faulty"}
    if intent == "damaged_item":
        return {"request": "damaged item", **replace_or_refund(shop, order, items, u.get("preference"), "damaged on arrival")}
    return {"request": "return", **refund(shop, order, items, "return within 30 days")}


def run(email, shop, llm):
    reqs = understand(email, llm)
    facts, cust = [], None
    if any(r["intent"] not in ("policy_question",) for r in reqs):
        cust = read(shop, "find_customer", email=email["sender"].lower())   # the policy: "letter case aside"
        if "error" in cust:
            return write_reply(email, [{"outcome": "sender_not_recognised",
                                        "ask": "write from the email address on your account"}], llm, False)
    for u in reqs:
        facts.append(handle(u, cust, shop))
    return write_reply(email, facts, llm, any(r["intent"] == "policy_question" for r in reqs))
