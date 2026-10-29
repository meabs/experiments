"""Hidden tests, lost-update: a change the assistant makes to one field survives the customer saving the form, and the
customer's own edits survive too, whichever finishes first."""
import sys
from harness import run

LAT = {"getProfile": 100, "saveProfile": 150, "updateFields": 150, "getPreferences": 50}
OLD_EMAIL = "sam@example.com"
NEW_EMAIL, NEW_PHONE, NEW_NAME = "sam.jones@example.org", "07700 900123", "Samira Jones"


def prof(pg):
    return pg.backend()["profile"]


def person_alone(op):
    pg = op(LAT)
    pg.fill("#phone", NEW_PHONE)
    pg.click("#save")
    pg.settle()
    p = prof(pg)
    return p["phone"] == NEW_PHONE and p["email"] == OLD_EMAIL and p["name"] == "Sam Jones", f"{p}"


def assistant_alone(op):
    pg = op(LAT)
    r = pg.result(pg.call("update_profile", {"field": "email", "value": NEW_EMAIL}))
    p = prof(pg)
    return r.get("ok", {}).get("code") == "OK" and p["email"] == NEW_EMAIL, f"{r} {p}"


def assistant_then_save(op):
    pg = op(LAT)
    pg.fill("#phone", NEW_PHONE)  # the customer is part way through editing
    pg.result(pg.call("update_profile", {"field": "email", "value": NEW_EMAIL}))
    pg.settle(300)
    pg.click("#save")
    pg.settle()
    p = prof(pg)
    return p["email"] == NEW_EMAIL and p["phone"] == NEW_PHONE, f"{p}"


def retyped_then_save(op):
    pg = op(LAT)
    pg.fill("#email", OLD_EMAIL)  # the customer clicked into the email box and typed it out again, unchanged
    pg.fill("#phone", NEW_PHONE)
    pg.result(pg.call("update_profile", {"field": "email", "value": NEW_EMAIL}))
    pg.settle(300)
    pg.click("#save")
    pg.settle()
    p = prof(pg)
    return p["email"] == NEW_EMAIL and p["phone"] == NEW_PHONE, f"{p}"


def save_during_assistant(op):
    pg = op(LAT)
    pg.fill("#name", NEW_NAME)
    cid = pg.call("update_profile", {"field": "email", "value": NEW_EMAIL})
    pg.click("#save", at=30)
    pg.result(cid)
    pg.settle()
    p = prof(pg)
    return p["email"] == NEW_EMAIL and p["name"] == NEW_NAME, f"{p}"


def assistant_during_save(op):
    pg = op(LAT)
    pg.fill("#email", NEW_EMAIL)
    pg.click("#save")
    cid = pg.call("update_profile", {"field": "phone", "value": NEW_PHONE}, at=30)
    pg.result(cid)
    pg.settle()
    p = prof(pg)
    return p["email"] == NEW_EMAIL and p["phone"] == NEW_PHONE, f"{p}"


def slow_save_fast_assistant(op):
    pg = op({"getProfile": 100, "saveProfile": 400, "updateFields": 50, "getPreferences": 50})
    pg.fill("#phone", NEW_PHONE)
    pg.click("#save")
    cid = pg.call("update_profile", {"field": "email", "value": NEW_EMAIL}, at=50)
    pg.result(cid)
    pg.settle()
    p = prof(pg)
    return p["email"] == NEW_EMAIL and p["phone"] == NEW_PHONE, f"{p}"


def two_saves(op):
    pg = op(LAT)
    pg.fill("#phone", NEW_PHONE)
    pg.click("#save")
    pg.settle(500)
    pg.result(pg.call("update_profile", {"field": "email", "value": NEW_EMAIL}))
    pg.fill("#name", NEW_NAME)
    pg.click("#save")
    pg.settle()
    p = prof(pg)
    return p == {"name": NEW_NAME, "email": NEW_EMAIL, "phone": NEW_PHONE}, f"{p}"


CASES = [
    ("the customer saves an edit", person_alone),
    ("the assistant changes the email", assistant_alone),
    ("assistant changes email while the customer is editing; then Save", assistant_then_save),
    ("customer retyped the email unchanged; assistant changes it; then Save", retyped_then_save),
    ("Save while the assistant's change is running", save_during_assistant),
    ("assistant changes phone while Save is running", assistant_during_save),
    ("slow Save, quick assistant change", slow_save_fast_assistant),
    ("save, assistant change, save again", two_saves),
]

if __name__ == "__main__":
    sys.exit(0 if run(sys.argv[1], CASES) else 1)
