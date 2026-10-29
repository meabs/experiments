"""Hidden tests, double-add: every add (a click, or an assistant call) puts the product in the basket once, also when the
shop is slow; a repeated add_to_cart with the same requestId adds once (while the first call is still running, after it
finished, after it was given up, and after the page was reloaded); separate adds all count."""
import sys
from harness import run

LAT = {"addItem": 150, "getBasket": 50, "getProducts": 50}
SLOW = {"addItem": 1200, "getBasket": 50, "getProducts": 50}


def qty(pg, sku="mug-01"):
    return pg.backend()["lines"].get(sku, 0)


def ok(r):
    return r.get("ok", {}).get("code") == "OK"


def one(op):
    pg = op(LAT)
    r = pg.result(pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}))
    return ok(r) and qty(pg) == 1, f"{r} {qty(pg)}"


def three(op):
    pg = op(LAT)
    r = pg.result(pg.call("add_to_cart", {"sku": "mug-01", "quantity": 3, "requestId": "r1"}))
    return ok(r) and qty(pg) == 3, f"{r} {qty(pg)}"


def repeat_overlapping(op):
    pg = op(LAT)
    a, b = pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}), pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}, at=40)
    ra, rb = pg.result(a), pg.result(b)
    pg.settle()
    return qty(pg) == 1 and "error" not in ra and "error" not in rb, f"{ra} {rb} {qty(pg)}"


def repeat_after(op):
    pg = op(LAT)
    ra = pg.result(pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}))
    rb = pg.result(pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}))
    pg.settle()
    return qty(pg) == 1 and "error" not in rb, f"{ra} {rb} {qty(pg)}"


def retry_after_giving_up(op):
    pg = op({"addItem": [400, 100], "getBasket": 50, "getProducts": 50})
    a = pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}, abort_ms=100)
    pg.result(a)
    rb = pg.result(pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}, at=150))
    pg.settle()
    return qty(pg) == 1 and "error" not in rb, f"{rb} {qty(pg)}"


def retry_after_reload(op):
    pg = op(LAT)
    pg.result(pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}))
    pg.reload()  # the customer refreshed the page before the assistant saw the answer
    rb = pg.result(pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}))
    pg.settle()
    return qty(pg) == 1 and "error" not in rb, f"{rb} {qty(pg)}"


def different_ids(op):
    pg = op(LAT)
    a, b = pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r1"}), pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r2"}, at=40)
    pg.result(a), pg.result(b)
    pg.settle()
    return qty(pg) == 2, f"{qty(pg)}"


def person_twice(op):
    pg = op(LAT)
    pg.click("#add-mug")
    pg.click("#add-mug", at=300)
    pg.settle()
    return qty(pg) == 2, f"{qty(pg)}"


def person_and_assistant(op):
    pg = op(LAT)
    cid = pg.call("add_to_cart", {"sku": "mug-01", "requestId": "r9"})
    pg.click("#add-mug", at=20)
    pg.result(cid)
    pg.settle()
    return qty(pg) == 2, f"{qty(pg)}"


def slow_click(op):
    pg = op(SLOW)
    pg.click("#add-mug")
    pg.settle(3000)
    return qty(pg) == 1, f"{qty(pg)}"


def slow_assistant(op):
    pg = op(SLOW)
    r = pg.result(pg.call("add_to_cart", {"sku": "tea-02", "requestId": "r1"}))
    pg.settle(2000)
    return ok(r) and qty(pg, "tea-02") == 1, f"{r} {qty(pg, 'tea-02')}"


def slow_two_clicks(op):
    pg = op(SLOW)
    pg.click("#add-mug")
    pg.click("#add-mug", at=100)
    pg.settle(3500)
    return qty(pg) == 2, f"{qty(pg)}"


CASES = [
    ("one add works", one),
    ("quantity 3 adds 3", three),
    ("same requestId repeated while the first runs", repeat_overlapping),
    ("same requestId repeated after the first finished", repeat_after),
    ("same requestId retried after the first call was given up", retry_after_giving_up),
    ("same requestId retried after the page was reloaded", retry_after_reload),
    ("different requestIds both add", different_ids),
    ("two clicks add two", person_twice),
    ("a click and an assistant add both count", person_and_assistant),
    ("slow shop: one click adds one", slow_click),
    ("slow shop: one assistant add adds one", slow_assistant),
    ("slow shop: two clicks add two", slow_two_clicks),
]

if __name__ == "__main__":
    sys.exit(0 if run(sys.argv[1], CASES) else 1)
