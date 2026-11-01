"""The 38 cases: need-an-agent's 32 (levels 1-5, unchanged) plus 6 new level-6 compound emails, written before any
architecture here was run. Each level-6 email has two or three requests that span both specialists' areas
(deliveries and order changes / returns, refunds and billing), so a crew has to hand over at least once.
"""
import re

import base  # noqa: F401
from cases import CASES as NA_CASES, HUMAN, R, P, ESC, d  # need-an-agent's cases.py (this file is crewcases.py)

L6 = [
    dict(id="L6-01", level=6, known=False, sender="priya.shah@mail.test", subject="A few things",
         body="Hi, three things. Could you change the delivery address for A1088 to 14 Elm Road, Leeds LS6 2AB? Also "
              "the mug set from A1042 arrived with one mug chipped, please send me a replacement set. And do you "
              "take American Express? Thanks, Priya",
         expect=dict(actions=[[{"type": "address", "order": "A1088"}, P("A1042", {"MUGSET-4": 1})]],
                     facts=[r"elm road|address", r"replace", r"american express|amex"])),
    dict(id="L6-02", level=6, known=False, sender="amira.haddad@mail.test", subject="Cancel and return",
         body="Please cancel A1077, I ordered it by mistake. I'd also like to return both speckled mugs from A1033 "
              "for a refund, they're unused. How long will the refunds take?",
         expect=dict(actions=[[{"type": "cancel", "order": "A1077"}, R("A1033", {"MUG-SPECK": 2})]],
                     facts=[r"cancel", r"24(\.00)?\b", r"5 working days|five working days"])),
    dict(id="L6-03", level=6, known=False, sender="tom.okafor@mail.test", subject="Orders",
         body="Hello. Where is A1051? I'd also like to return the velvet cushion from A0990, I've gone off it. And "
              "the wool blanket from A1052 arrived with a moth hole in it, so I'd like a refund for that please.",
         expect=dict(actions=[[R("A1052", {"BLANKET-WOOL": 1})]],
                     facts=[d(1, 11), r"30[- ]days?", r"45(\.00)?\b"])),
    dict(id="L6-04", level=6, known=False, sender="grace.liu@mail.test", subject="A1063",
         body="The jute rug from A1063 doesn't fit our room, so I'd like to return it. The bud vase in the same order "
              "arrived chipped, please replace it. Also, do you deliver to Ireland? My sister lives in Cork.",
         expect=dict(actions=[[ESC, P("A1063", {"VASE-GLASS": 1})]],
                     facts=[HUMAN, r"replace", r"9\.95"])),
    dict(id="L6-05", level=6, known=False, sender="leo.martin@mail.test", subject="Two orders",
         body="Tracking for A1081 hasn't moved for two weeks; I'd rather have my money back than wait for another. "
              "And A1080 says delivered, but it never came. Can I pay with PayPal next time?",
         expect=dict(actions=[[R("A1081", {"VASE-GLASS": 1}), ESC]],
                     facts=[r"refund", r"35(\.00)?\b", HUMAN, r"paypal"])),
    dict(id="L6-06", level=6, known=False, sender="ben.carter@mail.test", subject="Throw, frame and payment",
         body="The cotton throw from A1070 arrived torn. I'd also like to return the oak frame from A1071, I've "
              "changed my mind about it. And my bank shows two payments for A1071, can you check?",
         expect=dict(actions=[[R("A1070", {"THROW-CLR": 1}), R("A1071", {"FRAME-OAK": 1}), ESC]],
                     facts=[r"18(\.00)?\b", r"22(\.00)?\b", r"out of stock|not in stock|unavailable", HUMAN])),
]
for c in L6:
    c.setdefault("faults", [])
    for f in c["expect"]["facts"]:
        re.compile(f)

CASES = NA_CASES + L6
assert len({c["id"] for c in CASES}) == len(CASES) == 38
