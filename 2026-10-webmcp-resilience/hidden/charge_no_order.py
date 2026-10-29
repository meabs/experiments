"""Hidden tests, charge-no-order: whenever place_order is cancelled, every payment taken (and not refunded) has an order
and every order has a payment; a call cancelled before payment takes nothing; uncancelled orders and the button still
work."""
import sys
from harness import run

LAT = {"getQuote": 100, "charge": 150, "createOrder": 150, "refund": 100, "getAddresses": 50}


def code(r):
    return r.get("ok", {}).get("code")


def plain(op):
    pg = op(LAT)
    r = pg.result(pg.call("place_order"))
    pg.settle()
    b = pg.backend()
    return code(r) == "OK" and b["charges"] == 1 and b["orders"] == 1, f"{r} {b}"


def button(op):
    pg = op(LAT)
    pg.click("#place")
    pg.settle()
    b = pg.backend()
    return b["charges"] == 1 and b["orders"] == 1, f"{b}"


def cancel_before_payment(op):
    pg = op(LAT)
    r = pg.result(pg.call("place_order", abort_ms=50))
    pg.settle()
    b = pg.backend()
    return code(r) != "OK" and b["charges"] == 0 and b["orders"] == 0, f"{r} {b}"


def cancel_at(ms):
    def case(op):
        pg = op(LAT)
        r = pg.result(pg.call("place_order", abort_ms=ms))
        pg.settle()
        b = pg.backend()
        consistent = b["charges"] == b["orders"] and b["orders"] <= 1
        return consistent and (code(r) != "OK" or b["orders"] == 1), f"{r} {b}"
    return case


def cancel_then_again(op):
    pg = op(LAT)
    pg.result(pg.call("place_order", abort_ms=175))
    r = pg.result(pg.call("place_order", at=600))
    pg.settle()
    b = pg.backend()
    return code(r) == "OK" and b["charges"] == b["orders"] and b["orders"] >= 1, f"{r} {b}"


CASES = [
    ("an order without cancelling", plain),
    ("the Place order button", button),
    ("cancelled while pricing: nothing taken", cancel_before_payment),
    ("cancelled early in paying", cancel_at(130)),
    ("cancelled late in paying", cancel_at(230)),
    ("cancelled early in creating the order", cancel_at(270)),
    ("cancelled late in creating the order", cancel_at(380)),
    ("cancelled, then ordered again", cancel_then_again),
]

if __name__ == "__main__":
    sys.exit(0 if run(sys.argv[1], CASES) else 1)
