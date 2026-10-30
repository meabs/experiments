"""Architecture 2, one model call: the code gathers everything that might be relevant up front (the sender's account,
all their orders, tracking for each, stock for each item), then makes one call. The model returns the actions to take
and the reply; the code carries the actions out in order. No retries and no second look: if an action fails, the
code escalates and sends a holding reply instead.
"""
import json

from llm import parse_json
from shop import TODAY

POLICY = open(__file__.replace("single.py", "policy.md")).read()

SYSTEM = f"""You handle customer emails for Hartley & Finch, an online homeware shop. Today is {TODAY}.
Follow this policy exactly:

{POLICY}

You get the email and everything our systems hold about the sender. Decide what to do and return only a JSON object:
{{"actions": [ {{"tool": name, "args": {{...}}}} ], "reply": "the email to send the customer"}}
Tools you may use in "actions" (they run in order, after you answer):
- issue_refund {{"order_id", "items": [{{"sku", "quantity"}}], "reason"}}
- send_replacement {{"order_id", "items": [{{"sku", "quantity"}}], "reason"}}
- change_address {{"order_id", "address"}}
- cancel_order {{"order_id"}}
- escalate {{"team", "reason"}}
Use an empty list if nothing needs doing. The reply must state the outcome, amounts in £ and relevant dates."""

HOLDING = ("Hello,\n\nThanks for your message. We've passed it to a colleague, who will be in touch within 1 working "
           "day.\n\nHartley & Finch")


def gather(email, shop):
    ctx = {"customer": shop.call("find_customer", {"email": email["sender"]})}
    orders = ctx["customer"].get("orders", [])
    ctx["orders"], ctx["tracking"], ctx["stock"] = [], [], []
    for oid in orders:
        o = shop.call("get_order", {"order_id": oid})
        ctx["orders"].append(o)
        ctx["tracking"].append(shop.call("track_shipment", {"order_id": oid}))
        for it in o.get("items", []):
            ctx["stock"].append(shop.call("check_stock", {"sku": it["sku"]}))
    return ctx


def run(email, shop, llm):
    ctx = gather(email, shop)
    m = llm.chat([{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
                                              f"\n\nWhat our systems hold:\n{json.dumps(ctx, indent=1)}"}],
                 json_mode=True)
    d = parse_json(m.get("content"))
    if not d:
        shop.call("escalate", {"team": "support", "reason": "could not process automatically"})
        return HOLDING
    allowed = {"issue_refund", "send_replacement", "change_address", "cancel_order", "escalate"}
    for a in d.get("actions") or []:
        if a.get("tool") not in allowed:
            continue
        r = shop.call(a["tool"], a.get("args") or {})
        if "error" in r:
            shop.call("escalate", {"team": "support", "reason": f"{a['tool']} failed: {r['error']}"})
            return HOLDING
    return d.get("reply") or ""
