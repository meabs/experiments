"""The 32 customer emails, each with the outcome the policy requires. Written before any architecture was run.

Levels:
  1 simple: one lookup, or a policy question
  2 fixed multi-step: a clear refund or replacement, everything stated
  3 branching: the right outcome depends on what the lookups return (dates, final sale, £200, stock, sender, which order)
  4 recovery: a tool fails or the input is slightly wrong; the right outcome is the same as with no fault
  5 unanticipated: requests outside the four intents the workflow was built for (see README), still covered by policy
expect.actions: alternative lists of state changes; [] means "reply only, change nothing". Escalations match on type.
expect.facts: regular expressions that must all appear in the reply (case-insensitive).
known: whether the request is one of the workflow's four designed intents (delivery status, return/refund,
damaged item, policy question).
"""
import re

MONTHS = {9: "Sep(tember)?", 10: "Oct(ober)?", 11: "Nov(ember)?"}


def d(day, month):
    """A date in any common written form: 1 Nov, 1st November, November 1, 2026-11-01, 01/11."""
    m = MONTHS[month]
    return (rf"(\b{day}(st|nd|rd|th)?\s+{m}\b|\b{m}\.?\s+{day}(st|nd|rd|th)?\b|2026-{month:02d}-{day:02d}"
            rf"|\b0?{day}/{month:02d}\b)")


HUMAN = r"(colleague|team|manager|escalat|be in touch|get back to you|contact you|follow up|reach out|in touch)"
NONE = [[]]


def R(order, items):
    return {"type": "refund", "order": order, "items": items}


def P(order, items):
    return {"type": "replace", "order": order, "items": items}


ESC = {"type": "escalate"}

CASES = [
    # ---- Level 1: simple ----
    dict(id="L1-01", level=1, known=True, sender="tom.okafor@mail.test", subject="Order A1051",
         body="Hi, where is my order A1051? Thanks, Tom",
         expect=dict(actions=NONE, facts=[r"(transit|on (its|the) way|with the courier|dispatched|shipped)", d(1, 11)])),
    dict(id="L1-02", level=1, known=True, sender="sam.price@mail.test", subject="Shipping to Ireland",
         body="Hello, do you deliver to Ireland, and how much does it cost?",
         expect=dict(actions=NONE, facts=[r"\byes\b|we (do )?(ship|deliver)", r"9\.95"])),
    dict(id="L1-03", level=1, known=True, sender="grace.liu@mail.test", subject="Returns",
         body="How long do I have to send something back if I change my mind?",
         expect=dict(actions=NONE, facts=[r"30[- ]days?"])),
    dict(id="L1-04", level=1, known=True, sender="amira.haddad@mail.test", subject="A1033",
         body="Can you tell me if order A1033 has been delivered yet?",
         expect=dict(actions=NONE, facts=[r"deliver", d(18, 10)])),
    dict(id="L1-05", level=1, known=True, sender="ben.carter@mail.test", subject="Order status",
         body="What's the status of my order A1071 please?",
         expect=dict(actions=NONE, facts=[r"deliver", d(22, 10)])),
    dict(id="L1-06", level=1, known=True, sender="grace.liu@mail.test", subject="Payment",
         body="Can I pay with PayPal on your site?",
         expect=dict(actions=NONE, facts=[r"\byes\b|we (do )?accept|you can", r"paypal"])),

    # ---- Level 2: fixed multi-step ----
    dict(id="L2-01", level=2, known=True, sender="priya.shah@mail.test", subject="Return A1042",
         body="Hi, I'd like to return the linen tea towel from order A1042, I don't need it after all. Priya",
         expect=dict(actions=[[R("A1042", {"TOWEL-LIN": 1})]], facts=[r"refund", r"8(\.00)?\b"])),
    dict(id="L2-02", level=2, known=True, sender="ben.carter@mail.test", subject="Broken frame",
         body="The oak frame in order A1071 arrived with the glass cracked. Please refund it.",
         expect=dict(actions=[[R("A1071", {"FRAME-OAK": 1})]], facts=[r"refund"])),
    dict(id="L2-03", level=2, known=True, sender="sofia.rossi@mail.test", subject="Carafe broken",
         body="My glass carafe (order A1090) arrived in pieces. Could you send me a replacement please?",
         expect=dict(actions=[[P("A1090", {"CARAFE": 1})]], facts=[r"replace"])),
    dict(id="L2-04", level=2, known=True, sender="amira.haddad@mail.test", subject="Return",
         body="I'd like to return both speckled mugs from order A1033 for a refund. They're unused.",
         expect=dict(actions=[[R("A1033", {"MUG-SPECK": 2})]], facts=[r"refund", r"24(\.00)?\b"])),
    dict(id="L2-05", level=2, known=True, sender="tom.okafor@mail.test", subject="Returning blanket",
         body="Please can I return the wool throw blanket from A1052? It's not the colour I expected.",
         expect=dict(actions=[[R("A1052", {"BLANKET-WOOL": 1})]], facts=[r"refund", r"45(\.00)?\b"])),
    dict(id="L2-06", level=2, known=True, sender="grace.liu@mail.test", subject="Chipped vase",
         body="The glass bud vase from order A1063 arrived chipped. I'd like a refund for the vase please.",
         expect=dict(actions=[[R("A1063", {"VASE-GLASS": 1})]], facts=[r"refund", r"35(\.00)?\b"])),

    # ---- Level 3: branching ----
    dict(id="L3-01", level=3, known=True, sender="tom.okafor@mail.test", subject="Return cushion",
         body="I'd like to return the velvet cushion from order A0990, I've gone off the colour.",
         expect=dict(actions=NONE, facts=[r"30[- ]days?"])),
    dict(id="L3-02", level=3, known=True, sender="ben.carter@mail.test", subject="Return throw",
         body="I changed my mind about the cotton throw in A1070. Can I send it back for a refund?",
         expect=dict(actions=NONE, facts=[r"final[- ]sale|clearance"])),
    dict(id="L3-03", level=3, known=True, sender="grace.liu@mail.test", subject="Rug return",
         body="The jute rug from A1063 doesn't fit the room. I'd like to return it for a refund.",
         expect=dict(actions=[[ESC]], facts=[HUMAN])),
    dict(id="L3-04", level=3, known=True, sender="sofia.rossi@mail.test", subject="Bowl",
         body="The ceramic serving bowl in order A1091 arrived cracked. A replacement please.",
         expect=dict(actions=[[R("A1091", {"BOWL-SERVE": 1})]], facts=[r"out of stock|not in stock|unavailable",
                                                                         r"refund"])),
    dict(id="L3-05", level=3, known=True, sender="leo.martin@mail.test", subject="Never arrived",
         body="Tracking says A1080 was delivered but I never got it. Nothing in my porch or with neighbours.",
         expect=dict(actions=[[ESC]], facts=[HUMAN])),
    dict(id="L3-06", level=3, known=True, sender="priya.shah@mail.test", subject="Damaged mugs",
         body="The mug set I ordered recently arrived with two mugs smashed. I'd like my money back for it please.",
         expect=dict(actions=[[R("A1042", {"MUGSET-4": 1})]], facts=[r"refund", r"24(\.00)?\b"])),
    dict(id="L3-07", level=3, known=True, sender="leo.martin@mail.test", subject="A1081 stuck",
         body="Tracking for A1081 hasn't moved for two weeks. Please just send me another one.",
         expect=dict(actions=[[P("A1081", {"VASE-GLASS": 1})]], facts=[r"replace|another|new one|resend|re-send"])),
    dict(id="L3-08", level=3, known=True, sender="priya.s@othermail.test", subject="Refund A1042",
         body="Hi, this is Priya Shah. Please refund the tea towel on order A1042, I'm writing from my work email.",
         expect=dict(actions=NONE, facts=[r"(account|registered|original|the) e-?mail"])),

    # ---- Level 4: recovery ----
    dict(id="L4-01", level=4, known=True, sender="tom.okafor@mail.test", subject="Order A1051",
         body="Hi, any news on where order A1051 is?",
         faults=[{"tool": "track_shipment", "times": 1, "error": "503 tracking service unavailable, try again"}],
         expect=dict(actions=NONE, facts=[r"(transit|on (its|the) way|with the courier|dispatched|shipped)", d(1, 11)])),
    dict(id="L4-02", level=4, known=True, sender="priya.shah@mail.test", subject="Return tea towel",
         body="Please refund the linen tea towel from order #a-1042, I don't need it.",
         expect=dict(actions=[[R("A1042", {"TOWEL-LIN": 1})]], facts=[r"refund", r"8(\.00)?\b"])),
    dict(id="L4-03", level=4, known=True, sender="amira.haddad@mail.test", subject="Return mugs",
         body="I'd like to return both speckled mugs from A1033 for a refund please, they're unused.",
         faults=[{"tool": "issue_refund", "times": 1, "error": "504 payment provider timeout", "applies": True}],
         expect=dict(actions=[[R("A1033", {"MUG-SPECK": 2})]], facts=[r"refund"])),
    dict(id="L4-04", level=4, known=True, sender="sofia.rossi@mail.test", subject="Carafe broken",
         body="My carafe from order A1090 arrived broken, please send a new one.",
         faults=[{"tool": "send_replacement", "times": 1, "error": "503 warehouse service unavailable, try again"}],
         expect=dict(actions=[[P("A1090", {"CARAFE": 1})]], facts=[r"replace|new one|another"])),
    dict(id="L4-05", level=4, known=True, sender="ben.carter@mail.test", subject="Broken frame",
         body="The frame from A1071 came with cracked glass. Refund please.",
         faults=[{"tool": "get_order", "times": 1, "error": "500 internal server error"}],
         expect=dict(actions=[[R("A1071", {"FRAME-OAK": 1})]], facts=[r"refund"])),
    dict(id="L4-06", level=4, known=True, sender="Grace.Liu@Mail.test", subject="Vase",
         body="The bud vase in A1063 was chipped when it arrived, I'd like a refund for it.",
         expect=dict(actions=[[R("A1063", {"VASE-GLASS": 1})]], facts=[r"refund"])),

    # ---- Level 5: unanticipated (outside the workflow's four intents) ----
    dict(id="L5-01", level=5, known=False, sender="priya.shah@mail.test", subject="Address change",
         body="Could you change the delivery address for A1088 to 14 Elm Road, Leeds LS6 2AB? I've moved.",
         expect=dict(actions=[[{"type": "address", "order": "A1088"}]], facts=[r"elm road|address"])),
    dict(id="L5-02", level=5, known=False, sender="amira.haddad@mail.test", subject="Cancel please",
         body="I ordered A1077 by mistake. Please cancel it.",
         expect=dict(actions=[[{"type": "cancel", "order": "A1077"}]], facts=[r"cancel"])),
    dict(id="L5-03", level=5, known=False, sender="tom.okafor@mail.test", subject="Two things",
         body="Two things: where is A1051? And I'd like to return the wool blanket from A1052 for a refund.",
         expect=dict(actions=[[R("A1052", {"BLANKET-WOOL": 1})]], facts=[d(1, 11), r"refund"])),
    dict(id="L5-04", level=5, known=False, sender="daniel.novak@mail.test", subject="Charged twice",
         body="I've been charged twice for order A1095. Please sort this out.",
         expect=dict(actions=[[ESC]], facts=[HUMAN])),
    dict(id="L5-05", level=5, known=False, sender="amira.haddad@mail.test", subject="Hold my order",
         body="I'm away until 10 November. Can you hold order A1077 and send it after that?",
         expect=dict(actions=NONE, facts=[r"cancel|address"])),
    dict(id="L5-06", level=5, known=False, sender="sofia.rossi@mail.test", subject="Two broken items",
         body="The carafe from A1090 arrived broken, I'd prefer my money back rather than a replacement. The "
              "serving bowl from A1091 is cracked too; replace that one if you can.",
         expect=dict(actions=[[R("A1090", {"CARAFE": 1}), R("A1091", {"BOWL-SERVE": 1})]],
                     facts=[r"refund", r"out of stock|not in stock|unavailable"])),
]

for c in CASES:
    c.setdefault("faults", [])
    for f in c["expect"]["facts"]:
        re.compile(f)
assert len({c["id"] for c in CASES}) == len(CASES)
