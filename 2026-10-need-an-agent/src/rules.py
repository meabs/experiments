"""Architecture 1, plain code: no AI. core.py's control flow with keyword rules for the language work and template
replies. Costs nothing to run; understands only the phrasings its rules anticipate.
"""
import re

import core

DAMAGED = ("broken", "cracked", "chipped", "smashed", "damaged", "in pieces", "faulty")
NOT_RECEIVED = ("never got", "never arrived", "never received", "not received", "didn't arrive", "did not arrive")
STUCK = ("hasn't moved", "not moved", "stuck", "no movement")
RETURN = ("return", "refund", "send it back", "money back", "send back")
WHERE = ("where is", "where's", "status", "delivered yet", "tracking", "any news", "arrived yet")
REPLACE = ("replacement", "replace", "another one", "send me another", "new one", "send a new")
FAQ = [
    (("ireland",), "Yes, we deliver to Ireland. Delivery costs £9.95 and takes 3–5 working days. We don't ship anywhere "
                   "else outside the UK."),
    (("paypal", "pay with", "payment method", "visa", "mastercard", "amex"),
     "Yes, you can pay with PayPal. We also accept Visa, Mastercard and American Express."),
    (("how long", "send something back", "returns policy", "return policy", "change my mind"),
     "You can return unwanted items within 30 days of delivery for a refund. Final-sale (clearance) items can only be "
     "returned if they're faulty."),
]


def has(text, words):
    return any(w in text for w in words)


class Rules:
    def understand(self, email):
        t = email["body"].lower()
        m = re.search(r"\b([a-z]\d{4})\b", t)
        oid = m.group(1).upper() if m else None
        if has(t, DAMAGED):
            intent = "damaged_item"
        elif has(t, NOT_RECEIVED) or has(t, STUCK):
            intent = "delivery_status"
        elif has(t, RETURN) and oid or has(t, ("refund", "money back")):
            intent = "return_refund"
        elif has(t, WHERE) and oid:
            intent = "delivery_status"
        elif any(has(t, keys) for keys, _ in FAQ):
            intent = "policy_question"
        else:
            intent = "other"
        pref = "replacement" if has(t, REPLACE) else "refund" if has(t, ("refund", "money back")) else None
        problem = "not_received" if has(t, NOT_RECEIVED) else "no_movement" if has(t, STUCK) else None
        qty = 2 if "both" in t else None
        return {"intent": intent, "order_id": oid, "items": [{"name": t, "quantity": qty}], "preference": pref,
                "problem": problem}

    def answer_question(self, email):
        t = email["body"].lower()
        for keys, answer in FAQ:
            if has(t, keys):
                return f"Hello,\n\n{answer}\n\nBest wishes,\nHartley & Finch"
        return "Hello,\n\nThanks for your message. A colleague will be in touch within 1 working day.\n\nHartley & Finch"

    def write_reply(self, email, f):
        o = f["outcome"]
        if o == "tracking":
            if f["status"] == "delivered":
                body = f"Order {f['order']} was delivered on {f['delivered_on']}."
            elif f["status"] == "in_transit":
                body = f"Order {f['order']} is in transit with the courier, expected on {f.get('expected_delivery')}."
            else:
                body = f"Order {f['order']} is being prepared; it's expected to be dispatched on {f.get('expected_dispatch')}."
        elif o == "refunded":
            body = (f"We've refunded £{f['amount']:.2f} for the {', '.join(f['items'])}. It will go back to your original "
                    "payment method within 5 working days.")
            if f.get("note"):
                body = "Sorry, that item is out of stock, so we've refunded it instead. " + body
        elif o == "replacement_sent":
            body = f"We're sending you a replacement {', '.join(f['items'])} (order {f['replacement_order']})."
        elif o == "declined":
            body = ("Sorry, we can't accept this return: "
                    + ("our returns window is 30 days from delivery." if "30 days" in f["reason"]
                       else "it's a final-sale (clearance) item, which can only be returned if faulty."))
        elif o == "escalated":
            body = f"I've passed this to {f['team']}. A colleague will be in touch within 1 working day."
        elif o in ("sender_not_recognised", "not_your_order"):
            body = "For your security, please write to us from the email address on your account."
        elif o == "need_order_number":
            body = "Could you tell us the order number, please?"
        elif o == "need_item":
            body = "Could you tell us which item this is about, please?"
        else:
            body = f"Order {f.get('order')} hasn't been delivered yet (status: {f.get('status')})."
        return f"Hello,\n\n{body}\n\nBest wishes,\nHartley & Finch"


def run(email, shop, llm=None):
    return core.handle(email, shop, Rules())
