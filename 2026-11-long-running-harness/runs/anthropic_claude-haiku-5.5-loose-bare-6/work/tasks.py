#!/usr/bin/env python3
"""Command-line task manager. Data stored in tasks.json in the CWD."""
import argparse
import copy
import csv
import datetime
import io
import json
import os
import sys

DATA_FILE = "tasks.json"
MUTATING = {"add", "done", "delete", "edit"}


class Fail(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Fail(message)


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("next_id", 1)
    data.setdefault("tasks", [])
    data.setdefault("history", [])
    return data


def save(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_FILE)


def snapshot(data):
    return {"next_id": data["next_id"], "tasks": copy.deepcopy(data["tasks"])}


def validate_date(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise Fail("Invalid date: %s" % value)
    return value


def find(data, tid):
    for t in data["tasks"]:
        if t["id"] == tid:
            return t
    raise Fail("No such task: %s" % tid)


def task_line(t):
    parts = ["%d [%s] %s" % (t["id"], "x" if t["done"] else " ", t["title"])]
    if t["priority"] != "medium":
        parts.append("(%s)" % t["priority"])
    if t["tags"]:
        parts.append(" ".join("#" + g for g in t["tags"]))
    if t["due"]:
        parts.append("due:" + t["due"])
    return " ".join(parts)


def build_parser():
    p = _Parser(prog="tasks.py")
    sub = p.add_subparsers(dest="command", required=True, parser_class=_Parser)

    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--priority", default="medium")
    a.add_argument("--tag", action="append", default=[])
    a.add_argument("--due", default=None)

    l = sub.add_parser("list")
    l.add_argument("--sort", default=None)
    l.add_argument("--tag", default=None)
    l.add_argument("--overdue", action="store_true")
    l.add_argument("--today", default=None)

    d = sub.add_parser("done")
    d.add_argument("id", type=int)

    dl = sub.add_parser("delete")
    dl.add_argument("id", type=int)

    e = sub.add_parser("edit")
    e.add_argument("id", type=int)
    e.add_argument("--title", nargs="+", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")

    x = sub.add_parser("export")
    x.add_argument("--format", required=True)

    sub.add_parser("stats")
    sub.add_parser("undo")
    return p


def run(argv):
    args = build_parser().parse_args(argv)
    cmd = args.command
    out = []

    if cmd == "export":
        if args.format not in ("json", "csv"):
            raise Fail("Invalid format: %s" % args.format)

    if cmd == "undo":
        data = load()
        if not data["history"]:
            raise Fail("Nothing to undo")
        prev = data["history"].pop()
        data["next_id"] = prev["next_id"]
        data["tasks"] = prev["tasks"]
        save(data)
        return ["Undone"]

    data = load()
    tasks = data["tasks"]

    if cmd == "list":
        if args.sort not in (None, "priority"):
            raise Fail("Invalid sort: %s" % args.sort)
        today = args.today
        if args.today is not None:
            validate_date(args.today)
        if args.overdue and today is None:
            today = datetime.date.today().isoformat()
        sel = list(tasks)
        if args.tag is not None:
            sel = [t for t in sel if args.tag in t["tags"]]
        if args.overdue:
            sel = [t for t in sel if not t["done"] and t["due"]
                   and t["due"] < today]
        if args.sort == "priority":
            rank = {"high": 0, "medium": 1, "low": 2}
            sel = sorted(sel, key=lambda t: (rank[t["priority"]], t["id"]))
        if not sel:
            return ["No tasks"]
        return [task_line(t) for t in sel]

    if cmd == "search":
        needle = args.text.lower()
        hits = [t for t in tasks if needle in t["title"].lower()]
        if not hits:
            return ["No matches"]
        return [task_line(t) for t in hits]

    if cmd == "stats":
        done = sum(1 for t in tasks if t["done"])
        return ["open: %d" % (len(tasks) - done), "done: %d" % done,
                "total: %d" % len(tasks)]

    if cmd == "export":
        if args.format == "json":
            arr = [{"id": t["id"], "title": t["title"], "done": t["done"],
                    "priority": t["priority"], "tags": list(t["tags"]),
                    "due": t["due"]} for t in tasks]
            return [json.dumps(arr, indent=2)]
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            w.writerow([t["id"], t["title"], "true" if t["done"] else "false",
                        t["priority"], ";".join(t["tags"]), t["due"] or ""])
        return [buf.getvalue().rstrip("\n")]

    # Mutating commands: snapshot first, mutate, then save.
    if cmd == "add":
        if args.priority not in ("high", "medium", "low"):
            raise Fail("Invalid priority: %s" % args.priority)
        if args.due is not None:
            validate_date(args.due)
        before = snapshot(data)
        tid = data["next_id"]
        data["next_id"] = tid + 1
        tasks.append({"id": tid, "title": args.title, "done": False,
                      "priority": args.priority, "tags": list(args.tag),
                      "due": args.due})
        msg = ["Added %d" % tid]
    elif cmd == "done":
        t = find(data, args.id)
        before = snapshot(data)
        t["done"] = True
        msg = ["Done %d" % args.id]
    elif cmd == "delete":
        find(data, args.id)
        before = snapshot(data)
        data["tasks"] = [t for t in tasks if t["id"] != args.id]
        msg = ["Deleted %d" % args.id]
    elif cmd == "edit":
        t = find(data, args.id)
        before = snapshot(data)
        t["title"] = " ".join(args.title)
        msg = ["Edited %d" % args.id]
    else:
        raise Fail("Unknown command: %s" % cmd)

    data["history"].append(before)
    save(data)
    return msg


def main():
    try:
        lines = run(sys.argv[1:])
    except Fail as e:
        msg = str(e)
        if msg.startswith("No such task") or msg.startswith("Invalid") \
                or msg.startswith("Nothing"):
            print(msg, file=sys.stderr)
        else:
            print("error: " + msg, file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
