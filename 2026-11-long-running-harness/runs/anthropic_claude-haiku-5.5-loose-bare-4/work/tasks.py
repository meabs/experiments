#!/usr/bin/env python3
"""Command-line task manager. Data in tasks.json in the current directory."""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

DATA_FILE = "tasks.json"
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


class TaskError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise TaskError(message)


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
    return {"next_id": data["next_id"],
            "tasks": json.loads(json.dumps(data["tasks"]))}


def push_history(data):
    data["history"].append(snapshot(data))


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        raise TaskError("Invalid date: %s" % value)
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise TaskError("Invalid date: %s" % value)
    return value


def find(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    raise TaskError("No such task: %s" % task_id)


def parse_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise TaskError("No such task: %s" % value)


def format_line(t):
    parts = ["%d [%s] %s" % (t["id"], "x" if t["done"] else " ", t["title"])]
    if t["priority"] != "medium":
        parts.append("(%s)" % t["priority"])
    if t["tags"]:
        parts.append(" ".join("#" + tag for tag in t["tags"]))
    if t["due"]:
        parts.append("due:" + t["due"])
    return " ".join(parts)


def cmd_add(args, data):
    priority = args.priority
    if priority not in PRIORITY_RANK:
        raise TaskError("Invalid priority: %s" % priority)
    due = valid_date(args.due) if args.due is not None else None
    push_history(data)
    task = {
        "id": data["next_id"],
        "title": " ".join(args.title),
        "done": False,
        "priority": priority,
        "tags": list(args.tag or []),
        "due": due,
    }
    data["next_id"] += 1
    data["tasks"].append(task)
    save(data)
    return "Added %d" % task["id"]


def cmd_list(args, data):
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
    if not tasks:
        return "No tasks"
    return "\n".join(format_line(t) for t in tasks)


def cmd_done(args, data):
    tid = parse_id(args.id)
    find(data, tid)
    push_history(data)
    find(data, tid)["done"] = True
    save(data)
    return "Done %d" % tid


def cmd_delete(args, data):
    tid = parse_id(args.id)
    find(data, tid)
    push_history(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save(data)
    return "Deleted %d" % tid


def cmd_edit(args, data):
    tid = parse_id(args.id)
    find(data, tid)
    push_history(data)
    find(data, tid)["title"] = " ".join(args.title)
    save(data)
    return "Edited %d" % tid


def cmd_search(args, data):
    needle = args.text.lower()
    matches = [t for t in data["tasks"] if needle in t["title"].lower()]
    if not matches:
        return "No matches"
    return "\n".join(format_line(t) for t in matches)


def cmd_export(args, data):
    if args.format == "json":
        out = [{"id": t["id"], "title": t["title"], "done": t["done"],
                "priority": t["priority"], "tags": t["tags"],
                "due": t["due"]} for t in data["tasks"]]
        return json.dumps(out, indent=2)
    if args.format == "csv":
        buf = io.StringIO()
        buf.write("id,title,done,priority,tags,due\n")
        for t in data["tasks"]:
            row = [str(t["id"]), t["title"], "true" if t["done"] else "false",
                   t["priority"], ";".join(t["tags"]), t["due"] or ""]
            buf.write(",".join(row) + "\n")
        return buf.getvalue().rstrip("\n")
    raise TaskError("Invalid format: %s" % args.format)


def cmd_stats(args, data):
    total = len(data["tasks"])
    done = sum(1 for t in data["tasks"] if t["done"])
    return "open: %d\ndone: %d\ntotal: %d" % (total - done, done, total)


def cmd_undo(args, data):
    if not data["history"]:
        raise TaskError("Nothing to undo")
    prev = data["history"].pop()
    data["next_id"] = prev["next_id"]
    data["tasks"] = prev["tasks"]
    save(data)
    return "Undone"


def build_parser():
    p = _Parser(prog="tasks.py")
    sub = p.add_subparsers(dest="command")
    sub.required = True

    a = sub.add_parser("add")
    a.add_argument("title", nargs="+")
    a.add_argument("--priority", default="medium")
    a.add_argument("--tag", action="append")
    a.add_argument("--due")

    l = sub.add_parser("list")
    l.add_argument("--sort", choices=["priority"])
    l.add_argument("--tag")
    l.add_argument("--overdue", action="store_true")
    l.add_argument("--today")

    for name in ("done", "delete"):
        s = sub.add_parser(name)
        s.add_argument("id")

    e = sub.add_parser("edit")
    e.add_argument("id")
    e.add_argument("--title", nargs="+", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")

    x = sub.add_parser("export")
    x.add_argument("--format", default="json", choices=["json", "csv"])

    sub.add_parser("stats")
    sub.add_parser("undo")
    return p


COMMANDS = {
    "add": cmd_add, "list": cmd_list, "done": cmd_done,
    "delete": cmd_delete, "edit": cmd_edit, "search": cmd_search,
    "export": cmd_export, "stats": cmd_stats, "undo": cmd_undo,
}


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        data = load()
        out = COMMANDS[args.command](args, data)
        if out:
            print(out)
        return 0
    except TaskError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
