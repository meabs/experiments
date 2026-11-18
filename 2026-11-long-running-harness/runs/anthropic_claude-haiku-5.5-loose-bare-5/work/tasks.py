#!/usr/bin/env python3
"""Command-line task manager. Data is stored in tasks.json in the CWD."""
import argparse
import copy
import datetime
import json
import os
import sys

DATA_FILE = "tasks.json"
PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
MUTATING = ("add", "done", "delete", "edit")


class Error(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Error(message)


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


def push_history(data, snap):
    data["history"].append(snap)


def valid_date(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise Error("Invalid date: %s" % value)
    return value


def valid_priority(value):
    if value not in PRIORITIES:
        raise Error("Invalid priority: %s" % value)
    return value


def find_task(data, tid):
    for t in data["tasks"]:
        if t["id"] == tid:
            return t
    raise Error("No such task: %s" % tid)


def format_line(t):
    mark = "x" if t["done"] else " "
    parts = ["%d [%s] %s" % (t["id"], mark, t["title"])]
    if t["priority"] != "medium":
        parts.append("(%s)" % t["priority"])
    if t["tags"]:
        parts.append(" ".join("#" + tag for tag in t["tags"]))
    if t["due"]:
        parts.append("due:" + t["due"])
    return " ".join(parts)


def cmd_add(data, args):
    snap = snapshot(data)
    task = {
        "id": data["next_id"],
        "title": args.title,
        "done": False,
        "priority": args.priority,
        "tags": list(args.tag or []),
        "due": args.due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    push_history(data, snap)
    save(data)
    return "Added %d" % task["id"]


def cmd_list(data, args):
    tasks = list(data["tasks"])
    if args.tag:
        tasks = [t for t in tasks if args.tag in t["tags"]]
    if args.overdue:
        today = args.today or datetime.date.today().isoformat()
        valid_date(today)
        tasks = [t for t in tasks
                 if not t["done"] and t["due"] and t["due"] < today]
    if args.sort == "priority":
        tasks.sort(key=lambda t: (PRIORITY_RANK[t["priority"]], t["id"]))
    if not data["tasks"]:
        return "No tasks"
    if not tasks:
        return ""
    return "\n".join(format_line(t) for t in tasks)


def cmd_done(data, args):
    task = find_task(data, args.id)
    snap = snapshot(data)
    task["done"] = True
    push_history(data, snap)
    save(data)
    return "Done %d" % args.id


def cmd_delete(data, args):
    find_task(data, args.id)
    snap = snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != args.id]
    push_history(data, snap)
    save(data)
    return "Deleted %d" % args.id


def cmd_edit(data, args):
    task = find_task(data, args.id)
    snap = snapshot(data)
    task["title"] = args.title
    push_history(data, snap)
    save(data)
    return "Edited %d" % args.id


def cmd_search(data, args):
    needle = args.text.lower()
    matches = [t for t in data["tasks"] if needle in t["title"].lower()]
    if not matches:
        return "No matches"
    return "\n".join(format_line(t) for t in matches)


def cmd_export(data, args):
    tasks = data["tasks"]
    if args.format == "json":
        out = [
            {
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": list(t["tags"]),
                "due": t["due"],
            }
            for t in tasks
        ]
        return json.dumps(out, indent=2)
    lines = ["id,title,done,priority,tags,due"]
    for t in tasks:
        lines.append(",".join([
            str(t["id"]),
            t["title"],
            "true" if t["done"] else "false",
            t["priority"],
            ";".join(t["tags"]),
            t["due"] or "",
        ]))
    return "\n".join(lines)


def cmd_stats(data, args):
    total = len(data["tasks"])
    done = sum(1 for t in data["tasks"] if t["done"])
    return "open: %d\ndone: %d\ntotal: %d" % (total - done, done, total)


def cmd_undo(data, args):
    if not data["history"]:
        raise Error("Nothing to undo")
    snap = data["history"].pop()
    data["next_id"] = snap["next_id"]
    data["tasks"] = snap["tasks"]
    save(data)
    return "Undone"


def build_parser():
    p = Parser(prog="tasks.py")
    sub = p.add_subparsers(dest="command")
    sub.required = True

    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--priority", type=valid_priority, default="medium")
    a.add_argument("--tag", action="append")
    a.add_argument("--due", type=valid_date)

    l = sub.add_parser("list")
    l.add_argument("--sort", choices=["priority", "id"], default="id")
    l.add_argument("--tag")
    l.add_argument("--overdue", action="store_true")
    l.add_argument("--today")

    d = sub.add_parser("done")
    d.add_argument("id", type=int)

    de = sub.add_parser("delete")
    de.add_argument("id", type=int)

    e = sub.add_parser("edit")
    e.add_argument("id", type=int)
    e.add_argument("--title", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")

    ex = sub.add_parser("export")
    ex.add_argument("--format", choices=["json", "csv"], required=True)

    sub.add_parser("stats")
    sub.add_parser("undo")
    return p


HANDLERS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": cmd_undo,
}


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        data = load()
        out = HANDLERS[args.command](data, args)
    except Error as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
