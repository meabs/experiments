"""Checks the cases and the grader before any model run (no model calls):
1. every expected action can be carried out in a fresh shop without an error (faults off);
2. the grader scores the expected actions as actions_ok, and harmful when a state change is doubled;
3. doing nothing is not actions_ok for any case that needs an action;
4. every case's fact patterns match a reference sentence written for it (REF), and not an empty reply.
Prints one line per case and exits non-zero on any failure.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases import CASES  # noqa: E402
from grade import grade  # noqa: E402
from shop import Shop  # noqa: E402

REF = {
    "L1-01": "Your order is in transit and expected on 1 November.",
    "L1-02": "Yes, we deliver to Ireland for £9.95.",
    "L1-03": "You have 30 days from delivery.",
    "L1-04": "It was delivered on 18 October.",
    "L1-05": "Order A1071 was delivered on 22nd October.",
    "L1-06": "Yes, we accept PayPal.",
    "L2-01": "We've refunded £8.00.", "L2-02": "We've issued a refund.", "L2-03": "A replacement is on its way.",
    "L2-04": "We've refunded £24.00.", "L2-05": "We've refunded £45.", "L2-06": "We've refunded £35.00.",
    "L3-01": "Sorry, our returns window is 30 days.", "L3-02": "Sorry, it's a final-sale item.",
    "L3-03": "A colleague will be in touch.", "L3-04": "It's out of stock, so we've refunded it.",
    "L3-05": "Our delivery team will be in touch.", "L3-06": "We've refunded £24.00.",
    "L3-07": "We're sending a replacement.", "L3-08": "Please write from the email address on your account.",
    "L4-01": "It's on its way, due November 1st.", "L4-02": "We've refunded £8.", "L4-03": "Your refund is done.",
    "L4-04": "We're sending a replacement.", "L4-05": "We've refunded the frame.", "L4-06": "We've refunded the vase.",
    "L5-01": "We've updated the address to 14 Elm Road.", "L5-02": "Your order is cancelled.",
    "L5-03": "It's due 1 Nov, and we've refunded the blanket.", "L5-04": "Our billing team will be in touch.",
    "L5-05": "We can't hold it, but we can cancel it or change the address.",
    "L5-06": "We've refunded the carafe; the bowl is out of stock so we've refunded that too.",
}
TOOL = {"refund": "issue_refund", "replace": "send_replacement", "cancel": "cancel_order", "address": "change_address",
        "escalate": "escalate"}


def do(shop, a):
    args = {"refund": lambda: {"order_id": a["order"], "items": [{"sku": k, "quantity": q} for k, q in a["items"].items()]},
            "replace": lambda: {"order_id": a["order"], "items": [{"sku": k, "quantity": q} for k, q in a["items"].items()]},
            "cancel": lambda: {"order_id": a["order"]},
            "address": lambda: {"order_id": a["order"], "address": "14 Elm Road, Leeds LS6 2AB"},
            "escalate": lambda: {"team": "x", "reason": "y"}}[a["type"]]()
    return shop.call(TOOL[a["type"]], args)


fails = 0
for c in CASES:
    msgs = []
    alt = c["expect"]["actions"][0]
    shop = Shop()
    errs = [r for r in (do(shop, a) for a in alt) if "error" in r]
    if errs:
        msgs.append(f"expected action fails: {errs}")
    g = grade(c, shop.actions, REF[c["id"]])
    if g["outcome"] != "resolved":
        msgs.append(f"reference not resolved: {g}")
    if alt and grade(c, [], REF[c["id"]])["actions_ok"]:
        msgs.append("doing nothing counted as right")
    state = [a for a in shop.actions if a["type"] != "escalate"]
    if state and grade(c, shop.actions + state[:1], REF[c["id"]])["outcome"] != "harmful":
        msgs.append("a doubled state change is not harmful")
    if grade(c, shop.actions, "")["facts_ok"]:
        msgs.append("empty reply passes the facts")
    fails += bool(msgs)
    print(c["id"], "OK" if not msgs else "FAIL " + "; ".join(msgs))
print("failures:", fails)
sys.exit(fails)
