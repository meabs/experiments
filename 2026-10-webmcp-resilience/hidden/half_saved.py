"""Hidden tests, half-saved: a save that has started (from the assistant or the Save button) finishes in full when the
seller switches tab, is never left half done, the tool's answer matches what was saved, and each tab still offers only
its own tools."""
import sys
from harness import run

LAT = {"getListing": 50, "getStats": 50, "updateTitle": 150, "updateDescription": 150, "saveListing": 150}
OLD = {"title": "Oak bookshelf", "description": "Solid oak, 180 cm tall, five shelves."}
NEW = {"title": "Oak bookshelf, as new", "description": "Solid oak, 180 cm tall, five shelves. Collection only."}


def listing(pg):
    return pg.backend()["listing"]


def ok(r):
    return r.get("ok", {}).get("code") == "OK"


def plain(op):
    pg = op(LAT)
    r = pg.result(pg.call("save_listing", NEW))
    pg.settle()
    return ok(r) and listing(pg) == NEW, f"{r} {listing(pg)}"


def button(op):
    pg = op(LAT)
    pg.fill("#title", NEW["title"])
    pg.fill("#description", NEW["description"])
    pg.click("#save")
    pg.settle()
    return listing(pg) == NEW, f"{listing(pg)}"


def switch_at(ms):
    def case(op):
        pg = op(LAT)
        cid = pg.call("save_listing", NEW)
        pg.click("#tab-preview", at=ms)
        r = pg.result(cid)
        pg.settle()
        l = listing(pg)
        return ok(r) and l == NEW, f"{r} {l}"
    return case


def button_then_switch(ms):
    def case(op):
        pg = op(LAT)
        pg.fill("#title", NEW["title"])
        pg.fill("#description", NEW["description"])
        pg.click("#save")
        pg.click("#tab-preview", at=ms)
        pg.settle()
        return listing(pg) == NEW, f"{listing(pg)}"
    return case


def tabs_offer_own_tools(op):
    pg = op(LAT)
    editor = pg.tools()
    pg.click("#tab-preview")
    pg.settle(400)
    preview = pg.tools()
    pg.click("#tab-editor")
    pg.settle(400)
    back = pg.tools()
    r = pg.result(pg.call("save_listing", NEW))
    pg.settle()
    good = ("save_listing" in editor and "save_listing" not in preview and "get_listing" in preview
            and "save_listing" in back and "get_listing" not in back and ok(r) and listing(pg) == NEW)
    return good, f"editor {editor}, preview {preview}, back {back}, {r}"


CASES = [
    ("the assistant saves", plain),
    ("the Save button", button),
    ("switch to Preview early in the assistant's save", switch_at(60)),
    ("switch to Preview late in the assistant's save", switch_at(220)),
    ("Save button, then switch to Preview at once", button_then_switch(20)),
    ("Save button, then switch to Preview late in the save", button_then_switch(220)),
    ("each tab offers its own tools, and saving works after coming back", tabs_offer_own_tools),
]

if __name__ == "__main__":
    sys.exit(0 if run(sys.argv[1], CASES) else 1)
