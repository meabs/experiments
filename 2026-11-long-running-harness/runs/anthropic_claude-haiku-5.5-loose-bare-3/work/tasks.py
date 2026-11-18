#!/usr/bin/env python3
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

DATA_FILE = "tasks.json"
PRIORITIES = ("high", "medium", "low")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Fail(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Fail(message)


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "undo": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, DATA_FILE)


def snapshot(state):
    return {"next_id": state["next_id"], "tasks": json.loads(json.dumps(state["tasks"]))}


def push_undo(state):
    state["undo"].append(snapshot(state))


def valid_date(value):
    if not DATE_RE.match(value):
        raise Fail("Invalid date: %s" % value)
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise Fail("Invalid date: %s" % value)
    return value


def find(state, tid):
    for t in state["tasks"]:
        if t["id"] == tid:
            return t
    raise Fail("No such task: %d" % tid)


def format_line(t):
    parts = ["%d [%s] %s" % (t["id"], "x" if t["done"] else " ", t["title"])]
    if t["priority"] != "medium":
        parts.append("(%s)" % t["priority"])
    if t["tags"]:
        parts.append(" ".join("#" + g for g in t["tags"]))
    if t.get("due"):
        parts.append("due:" + t["due"])
    return " ".join(parts)


def cmd_add(state, a):
    priority = a.priority
    if priority not in PRIORITIES:
        raise Fail("Invalid priority: %s" % priority)
    due = valid_date(a.due) if a.due is not None else None
    push_undo(state)
    tid = state["next_id"]
    state["next_id"] += 1
    state["tasks"].append({
        "id": tid, "title": " ".join(a.title), "done": False,
        "priority": priority, "tags": list(a.tag or []), "due": due,
    })
    save(state)
    print("Added %d" % tid)


def cmd_list(state, a):
    tasks = list(state["tasks"])
    if a.tag:
        tasks = [t for t in tasks if a.tag in t["tags"]]
    if a.overdue:
        today = a.today or datetime.date.today().isoformat()
        valid_date(today)
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]
    if a.sort == "priority":
        rank = {p: i for i, p in enumerate(PRIORITIES)}
        tasks.sort(key=lambda t: (rank[t["priority"]], t["id"]))
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(format_line(t))


def cmd_done(state, a):
    t = find(state, a.id)
    push_undo(state)
    t["done"] = True
    save(state)
    print("Done %d" % a.id)


def cmd_delete(state, a):
    find(state, a.id)
    push_undo(state)
    state["tasks"] = [t for t in state["tasks"] if t["id"] != a.id]
    save(state)
    print("Deleted %d" % a.id)


def cmd_edit(state, a):
    find(state, a.id)
    push_undo(state)
    for t in state["tasks"]:
        if t["id"] == a.id:
            t["title"] = " ".join(a.title)
    save(state)
    print("Edited %d" % a.id)


def cmd_search(state, a):
    needle = a.text.lower()
    matches = [t for t in state["tasks"] if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_line(t))


def cmd_export(state, a):
    if a.format == "json":
        out = [{"id": t["id"], "title": t["title"], "done": t["done"],
                "priority": t["priority"], "tags": t["tags"], "due": t["due"]}
               for t in state["tasks"]]
        print(json.dumps(out, indent=2))
    else:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in state["tasks"]:
            w.writerow([t["id"], t["title"], "true" if t["done"] else "false",
                        t["priority"], ";".join(t["tags"]), t["due"] or ""])
        sys.stdout.write(buf.getvalue())


def cmd_stats(state, a):
    total = len(state["tasks"])
    done = sum(1 for t in state["tasks"] if t["done"])
    print("open: %d" % (total - done))
    print("done: %d" % done)
    print("total: %d" % total)


def cmd_undo(state, a):
    if not state["undo"]:
        raise Fail("Nothing to undo")
    prev = state["undo"].pop()
    state["next_id"] = prev["next_id"]
    state["tasks"] = prev["tasks"]
    save(state)
    print("Undone")


def build_parser():
    p = Parser(prog="tasks.py")
    sub = p.add_subparsers(dest="command")
    sub.required = True

    s = sub.add_parser("add")
    s.add_argument("title", nargs="+")
    s.add_argument("--priority", default="medium")
    s.add_argument("--tag", action="append")
    s.add_argument("--due")

    s = sub.add_parser("list")
    s.add_argument("--sort", choices=["priority"])
    s.add_argument("--tag")
    s.add_argument("--overdue", action="store_true")
    s.add_argument("--today")

    s = sub.add_parser("done")
    s.add_argument("id", type=int)

    s = sub.add_parser("delete")
    s.add_argument("id", type=int)

    s = sub.add_parser("edit")
    s.add_argument("id", type=int)
    s.add_argument("--title", nargs="+", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")

    s = sub.add_parser("export")
    s.add_argument("--format", choices=["json", "csv"], required=True)

    sub.add_parser("stats")
    sub.add_parser("undo")
    return p


COMMANDS = {
    "add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete,
    "edit": cmd_edit, "search": cmd_search, "export": cmd_export,
    "stats": cmd_stats, "undo": cmd_undo,
}


def main(argv):
    try:
        args = build_parser().parse_args(argv)
        state = load()
        COMMANDS[args.command](state, args)
        return 0
    except Fail as e:
        print(str(e), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError) as e:
        print("Error: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
