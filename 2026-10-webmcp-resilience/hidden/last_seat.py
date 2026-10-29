"""Hidden tests, last-seat: a class never ends up with more bookings than seats, whether the other booking comes from
the person on the page, a second assistant call, or another customer booking through the gym's app; and booking still
works when seats are free (two free seats can both be taken at once, a full class answers FULL)."""
import sys
from harness import run

LAT = {"getClass": 100, "createBooking": 100, "listClasses": 50}
SPIN = "spin-sat"


def seed(capacity, booked=()):
    return {"classes": [{"id": SPIN, "name": "Saturday spin class", "capacity": capacity},
                        {"id": "yoga-sun", "name": "Sunday yoga", "capacity": 12}],
            "bookings": [{"id": f"x{i}", "classId": SPIN, "name": n} for i, n in enumerate(booked)]}


def spin(pg):
    return pg.backend()[SPIN]


def code(r):
    return r.get("ok", {}).get("code")


def single(op):
    pg = op(LAT)
    r = pg.result(pg.call("book_seat", {"name": "Ana"}))
    b = spin(pg)
    return code(r) == "OK" and b["booked"] == 1, f"{r} {b}"


def full(op):
    pg = op(LAT, seed(1, ["Lee"]))
    r = pg.result(pg.call("book_seat", {"name": "Ana"}))
    b = spin(pg)
    return code(r) == "FULL" and b["booked"] == 1, f"{r} {b}"


def race(tool_at, click_at, lat):
    def case(op):
        pg = op(lat)
        cid = pg.call("book_seat", {"name": "Ana"}, at=tool_at)
        pg.click("#book", at=click_at)
        r = pg.result(cid)
        pg.settle()
        b = spin(pg)
        return b["booked"] == 1 and "error" not in r, f"tool {r}, backend {b}"
    return case


def two_tools(op):
    pg = op(LAT)
    a, c = pg.call("book_seat", {"name": "Ana"}), pg.call("book_seat", {"name": "Bo"}, at=20)
    ra, rc = pg.result(a), pg.result(c)
    b = spin(pg)
    return b["booked"] == 1 and sorted([code(ra), code(rc)]) == ["FULL", "OK"], f"{ra} {rc} {b}"


def two_seats(op):
    pg = op(LAT, seed(2))
    cid = pg.call("book_seat", {"name": "Ana"})
    pg.click("#book", at=10)
    r = pg.result(cid)
    pg.settle()
    b = spin(pg)
    return b["booked"] == 2 and code(r) == "OK", f"{r} {b}"


def other_customer(capacity, in_ms):
    """Another customer books through the gym's app while the assistant's booking is going through."""
    def case(op):
        pg = op(LAT, seed(capacity))
        cid = pg.call("book_seat", {"name": "Ana"})
        pg.eval("([c, ms]) => window.__backend.otherCustomerBooks(c, 'Kim', ms)", [SPIN, in_ms])
        r = pg.result(cid)
        pg.settle()
        b = spin(pg)
        if capacity == 1:
            ok = b["booked"] == 1 and (code(r) == "FULL") == ("Ana" not in b["names"])
        else:
            ok = b["booked"] == 2 and code(r) == "OK" and "Ana" in b["names"]
        return ok, f"tool {r}, backend {b}"
    return case


CASES = [
    ("one booking works", single),
    ("a full class answers FULL", full),
    ("person and assistant at once, same moment", race(0, 0, LAT)),
    ("person 60 ms after the assistant", race(0, 60, LAT)),
    ("assistant 60 ms after the person", race(60, 0, LAT)),
    ("person during a slow server write", race(0, 150, {"getClass": 50, "createBooking": 300, "listClasses": 50})),
    ("two assistant calls at once", two_tools),
    ("two free seats, both booked at once", two_seats),
    ("another customer takes the last seat in the app meanwhile", other_customer(1, 150)),
    ("another customer books one of two seats meanwhile", other_customer(2, 150)),
]

if __name__ == "__main__":
    sys.exit(0 if run(sys.argv[1], CASES) else 1)
