#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        if "tasks" not in data:
            data["tasks"] = []
        if "history" not in data:
            data["history"] = []
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "history": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    p = task.get("priority", "medium")
    if p == "high":
        line += " (high)"
    elif p == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            i += 1
            val = args[i]
            if val not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(val))
            priority = val
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            i += 1
            tags.append(args[i])
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            i += 1
            val = args[i]
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: {}".format(val))
            due = val
        else:
            title_parts.append(arg)
        i += 1

    title = " ".join(title_parts)
    if not title:
        error("add requires a TITLE")

    nid = next_id(data["tasks"])

    # Save state for undo before mutation
    data["history"].append({
        "type": "add",
        "state": {
            "tasks": [dict(t) for t in data["tasks"]],
            "next_id": nid,
        }
    })

    task = {
        "id": nid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    data["tasks"].append(task)
    save_data(data)
    print("Added {}".format(nid))


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"])

    sort_by = None
    tag_filter = None
    show_overdue = False
    overdue_today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            i += 1
            sort_by = args[i]
            if sort_by not in ("priority",):
                error("Unknown sort option: {}".format(sort_by))
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            i += 1
            tag_filter = args[i]
        elif arg == "--overdue":
            show_overdue = True
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a date value")
            i += 1
            overdue_today = args[i]
        else:
            error("Unknown option: {}".format(arg))
        i += 1

    if show_overdue:
        if overdue_today:
            try:
                today = datetime.strptime(overdue_today, "%Y-%m-%d").date()
            except ValueError:
                error("Invalid date: {}".format(overdue_today))
        else:
            today = date.today()

    filtered = list(tasks)

    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    if show_overdue:
        filtered = [
            t for t in filtered
            if not t["done"]
            and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    if sort_by == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for t in filtered:
        print(task_line(t))


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        tid = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))

    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        error("No such task: {}".format(tid))

    data["history"].append({
        "type": "done",
        "state": {
            "tasks": [dict(t) for t in data["tasks"]],
            "next_id": next_id(data["tasks"]),
        }
    })

    task["done"] = True
    save_data(data)
    print("Done {}".format(tid))


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        tid = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))

    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        error("No such task: {}".format(tid))

    data["history"].append({
        "type": "delete",
        "state": {
            "tasks": [dict(t) for t in data["tasks"]],
            "next_id": next_id(data["tasks"]),
        }
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print("Deleted {}".format(tid))


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        tid = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))

    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        error("No such task: {}".format(tid))

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            i += 1
            parts = []
            while i < len(args) and args[i] != "--title":
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            continue
        else:
            error("Unknown option: {}".format(args[i]))
        i += 1

    if new_title is None:
        error("--title is required")

    data["history"].append({
        "type": "edit",
        "state": {
            "tasks": [dict(t) for t in data["tasks"]],
            "next_id": next_id(data["tasks"]),
        }
    })

    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(tid))


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")

    data = load_data()
    query = " ".join(args).lower()

    matches = []
    for t in data["tasks"]:
        if query in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
        return

    matches.sort(key=lambda t: t["id"])
    for t in matches:
        print(task_line(t))


def cmd_export(args):
    fmt = None

    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            i += 1
            fmt = args[i]
            if fmt not in ("json", "csv"):
                error("Invalid format: {}".format(fmt))
        else:
            error("Unknown option: {}".format(args[i]))
        i += 1

    if fmt is None:
        error("Usage: export --format json|csv")

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_val = t.get("due") or ""
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                tags_str,
                due_val
            ))


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    data = load_data()

    if not data["history"]:
        error("Nothing to undo")

    last = data["history"].pop()
    state = last["state"]
    data["tasks"] = state["tasks"]
    save_data(data)
    print("Undone")


COMMANDS = {
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


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error("Unknown command: {}".format(command))

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
