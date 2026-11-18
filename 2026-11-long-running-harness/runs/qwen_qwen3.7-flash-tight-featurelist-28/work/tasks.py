#!/usr/bin/env python3
"""A command-line task manager."""

import argparse
import csv
import io
import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    for tag in task["tags"]:
        parts.append(f"#{tag}")
    if task["due"]:
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def validate_priority(value):
    if value not in ("high", "medium", "low"):
        print(f"Invalid priority: {value}", file=sys.stderr)
        sys.exit(1)
    return value


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        print(f"Invalid date: {value}", file=sys.stderr)
        sys.exit(1)


def cmd_add(args):
    data = load_data()
    priority = validate_priority(args.priority) if args.priority else "medium"
    tags = list(args.tag) if args.tag else []
    due = validate_date(args.due) if args.due else None
    task = {
        "id": data["next_id"],
        "title": args.title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    data["history"].append({"type": "add", "task": task})
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = data["tasks"][:]
    if not tasks:
        print("No tasks")
        return
    if args.tag:
        tasks = [t for t in tasks if args.tag in t["tags"]]
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_str]
    if not tasks:
        print("No tasks")
        return
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    for task in tasks:
        print(task_line(task))


def _find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_done(args):
    data = load_data()
    task = _find_task(data, args.id)
    data["history"].append({"type": "done", "task": dict(task)})
    task["done"] = True
    save_data(data)
    print(f"Done {args.id}")


def cmd_delete(args):
    data = load_data()
    task = _find_task(data, args.id)
    data["history"].append({"type": "delete", "task": dict(task)})
    data["tasks"] = [t for t in data["tasks"] if t["id"] != args.id]
    save_data(data)
    print(f"Deleted {args.id}")


def cmd_edit(args):
    data = load_data()
    task = _find_task(data, args.id)
    data["history"].append({"type": "edit", "task": dict(task)})
    task["title"] = args.title
    save_data(data)
    print(f"Edited {args.id}")


def cmd_search(args):
    data = load_data()
    query = args.text.lower()
    results = [t for t in data["tasks"] if query in t["title"].lower()]
    if not results:
        print("No matches")
        return
    for task in results:
        print(task_line(task))


def cmd_export(args):
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if args.format == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output, indent=2))
    elif args.format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(buf.getvalue(), end="")


def cmd_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    entry = data["history"].pop()
    etype = entry["type"]
    task = entry["task"]
    if etype == "add":
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task["id"]]
        data["next_id"] = task["id"]
    elif etype == "done":
        for t in data["tasks"]:
            if t["id"] == task["id"]:
                t["done"] = False
                break
    elif etype == "delete":
        data["tasks"].append(task)
        data["next_id"] = task["id"]
    elif etype == "edit":
        for t in data["tasks"]:
            if t["id"] == task["id"]:
                t["title"] = task["title"]
                break
    save_data(data)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    add_p = subparsers.add_parser("add")
    add_p.add_argument("title")
    add_p.add_argument("--priority", default=None)
    add_p.add_argument("--tag", action="append", default=None)
    add_p.add_argument("--due", default=None)

    list_p = subparsers.add_parser("list")
    list_p.add_argument("--sort", default=None)
    list_p.add_argument("--tag", default=None)
    list_p.add_argument("--overdue", action="store_true")
    list_p.add_argument("--today", default=None)

    done_p = subparsers.add_parser("done")
    done_p.add_argument("id", type=int)

    delete_p = subparsers.add_parser("delete")
    delete_p.add_argument("id", type=int)

    edit_p = subparsers.add_parser("edit")
    edit_p.add_argument("id", type=int)
    edit_p.add_argument("--title", required=True)

    search_p = subparsers.add_parser("search")
    search_p.add_argument("text")

    export_p = subparsers.add_parser("export")
    export_p.add_argument("--format", required=True)

    subparsers.add_parser("stats")
    subparsers.add_parser("undo")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
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
    commands[args.command](args)


if __name__ == "__main__":
    main()
