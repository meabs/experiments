"""Checks the six new level-6 cases and the grading change before any model run (no model calls), as need-an-agent's
validate.py does for its 32: expected actions run without error; the reference reply scores resolved; doing nothing
isn't right; a doubled state change is harmful; an empty reply fails the facts; and (new) a second escalation in the
same run doesn't change the grade. Exits non-zero on any failure.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402,F401
from crewcases import L6  # noqa: E402
from run import grade  # noqa: E402
from shop import Shop  # noqa: E402

REF = {
    "L6-01": "We've changed the address to 14 Elm Road and are sending a replacement mug set. We accept American Express.",
    "L6-02": "Order A1077 is cancelled and we've refunded £24.00 for the mugs; refunds take up to 5 working days.",
    "L6-03": "A1051 is due on 1 November. The cushion is outside our 30-day returns window. We've refunded £45.00.",
    "L6-04": "A manager will be in touch about the rug. We're sending a replacement vase. Ireland delivery is £9.95.",
    "L6-05": "We've refunded £35.00 for A1081. Our delivery team will be in touch about A1080. Yes, we accept PayPal.",
    "L6-06": "The throw is out of stock, so we've refunded £18.00; we've refunded £22.00 for the frame; our billing "
             "team will be in touch.",
}
TOOL = {"refund": "issue_refund", "replace": "send_replacement", "cancel": "cancel_order", "address": "change_address",
        "escalate": "escalate"}


def do(shop, a):
    items = lambda: [{"sku": k, "quantity": q} for k, q in a["items"].items()]
    args = {"refund": lambda: {"order_id": a["order"], "items": items()},
            "replace": lambda: {"order_id": a["order"], "items": items()},
            "cancel": lambda: {"order_id": a["order"]},
            "address": lambda: {"order_id": a["order"], "address": "14 Elm Road, Leeds LS6 2AB"},
            "escalate": lambda: {"team": "x", "reason": "y"}}[a["type"]]()
    return shop.call(TOOL[a["type"]], args)


fails = 0
for c in L6:
    msgs, alt, shop = [], c["expect"]["actions"][0], Shop()
    errs = [r for r in (do(shop, a) for a in alt) if "error" in r]
    if errs:
        msgs.append(f"expected action fails: {errs}")
    g = grade(c, shop.actions, REF[c["id"]])
    if g["outcome"] != "resolved":
        msgs.append(f"reference not resolved: {g}")
    if grade(c, [], REF[c["id"]])["actions_ok"]:
        msgs.append("doing nothing counted as right")
    state = [a for a in shop.actions if a["type"] != "escalate"]
    if state and grade(c, shop.actions + state[:1], REF[c["id"]])["outcome"] != "harmful":
        msgs.append("a doubled state change is not harmful")
    for drop in state:   # leaving out any one required action isn't right
        if grade(c, [a for a in shop.actions if a is not drop], REF[c["id"]])["actions_ok"]:
            msgs.append(f"missing {drop['type']} still counted as right")
    esc = [a for a in shop.actions if a["type"] == "escalate"]
    if esc and grade(c, shop.actions + esc[:1], REF[c["id"]])["outcome"] != "resolved":
        msgs.append("a second escalation changes the grade")
    if grade(c, shop.actions, "")["facts_ok"]:
        msgs.append("empty reply passes the facts")
    fails += bool(msgs)
    print(c["id"], "OK" if not msgs else "FAIL " + "; ".join(msgs))
print("failures:", fails)
sys.exit(fails)
