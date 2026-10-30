"""Architecture 3, workflow: core.py's fixed control flow, with the model doing the language work at fixed points.
  1. understand: one call turns the email into structured fields (JSON);
  2. the code looks things up, applies the policy's rules and takes any action (core.py);
  3. write_reply: one call writes the reply from the facts the code decided. Policy questions get one call with the
     policy. So 2 model calls per email, 1 for a policy question, never a loop.
"""
import json

import core
from llm import parse_json
from shop import TODAY

POLICY = open(__file__.replace("workflow.py", "policy.md")).read()

UNDERSTAND = """You read customer emails for Hartley & Finch, an online homeware shop. Return only a JSON object:
{"intent": one of "delivery_status" (where is my order, it never arrived, tracking not moving), "return_refund"
 (wants to return an item or get a refund, item not damaged), "damaged_item" (item arrived damaged or faulty),
 "policy_question" (a general question about delivery, returns or payment, about no particular order), "other"
 (anything else),
 "order_id": the order number mentioned (e.g. "A1042") or null,
 "items": [{"name": item as the customer describes it, "quantity": number or null}],
 "preference": "refund", "replacement" or null (what they ask for, if they say),
 "problem": for delivery_status only: "where_is", "not_received" or "no_movement"; otherwise null}"""

REPLY = """You write replies to customers for Hartley & Finch, an online homeware shop. Write a short, friendly email
reply. The facts below are what our system has decided and done: state every fact that matters to the customer
(amounts in £, dates, statuses, what happens next). Do not promise or decide anything that is not in the facts.
Sign off as Hartley & Finch."""


class Workflow:
    def __init__(self, llm):
        self.llm = llm

    def understand(self, email):
        m = self.llm.chat([{"role": "system", "content": UNDERSTAND},
                           {"role": "user", "content": f"Subject: {email['subject']}\n\n{email['body']}"}],
                          json_mode=True)
        return parse_json(m.get("content")) or {"intent": "other"}

    def answer_question(self, email):
        m = self.llm.chat([{"role": "system", "content": f"{REPLY}\n\nAnswer the customer's question from this policy "
                                                        f"only. Today is {TODAY}.\n\n{POLICY}"},
                           {"role": "user", "content": f"Subject: {email['subject']}\n\n{email['body']}"}])
        return m.get("content") or ""

    def write_reply(self, email, facts):
        m = self.llm.chat([{"role": "system", "content": REPLY},
                           {"role": "user", "content": f"Customer's email:\nSubject: {email['subject']}\n\n{email['body']}"
                                                       f"\n\nFacts (today is {TODAY}):\n{json.dumps(facts)}"}])
        return m.get("content") or ""


def run(email, shop, llm):
    return core.handle(email, shop, Workflow(llm))
