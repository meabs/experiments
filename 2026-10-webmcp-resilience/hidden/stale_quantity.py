"""Hidden tests, stale-quantity: after changes from the buttons and the assistant overlap, the saved quantity is the
last one asked for, and the page shows what is saved."""
import sys
from harness import run

BASE = {"getLine": 50, "getStock": 50}


def lat(set_quantity):
    return {**BASE, "setQuantity": set_quantity}


def state(pg):
    q = pg.backend()["lines"]["tea-02"]
    shown = int(pg.text("#quantity"))
    return q, shown


def ends(expected, setup):
    def case(op):
        pg = setup(op)
        pg.settle()
        q, shown = state(pg)
        return q == expected and shown == expected, f"saved {q}, shown {shown}, expected {expected}"
    return case


def plus(op):
    pg = op(lat(120))
    pg.click("#plus")
    return pg


def tool5(op):
    pg = op(lat(120))
    pg.result(pg.call("set_quantity", {"sku": "tea-02", "quantity": 5}))
    return pg


def slow_click_fast_tool(op):
    pg = op(lat([400, 50]))
    pg.click("#plus")
    pg.call("set_quantity", {"sku": "tea-02", "quantity": 5}, at=50)
    return pg


def slow_tool_fast_click(op):
    pg = op(lat([400, 50]))
    pg.call("set_quantity", {"sku": "tea-02", "quantity": 5})
    pg.click("#plus", at=50)  # the customer sees 5 and asks for one more
    return pg


def two_tools(op):
    pg = op(lat([400, 50]))
    pg.call("set_quantity", {"sku": "tea-02", "quantity": 3})
    pg.call("set_quantity", {"sku": "tea-02", "quantity": 7}, at=50)
    return pg


def two_clicks(op):
    pg = op(lat([300, 50]))
    pg.click("#plus")
    pg.click("#plus", at=50)
    return pg


def click_tool_click(op):
    pg = op(lat([500, 300, 50]))
    pg.click("#plus")                                                   # 2, slowest
    pg.call("set_quantity", {"sku": "tea-02", "quantity": 8}, at=40)    # 8
    pg.click("#minus", at=80)                                           # 7, quickest
    return pg


CASES = [
    ("one click", ends(2, plus)),
    ("one assistant change", ends(5, tool5)),
    ("slow click, then a quick assistant change", ends(5, slow_click_fast_tool)),
    ("slow assistant change, then a quick click", ends(6, slow_tool_fast_click)),
    ("two assistant changes, the first slow", ends(7, two_tools)),
    ("two quick clicks, the first slow", ends(3, two_clicks)),
    ("click, assistant change, click, finishing in reverse", ends(7, click_tool_click)),
]

if __name__ == "__main__":
    sys.exit(0 if run(sys.argv[1], CASES) else 1)
