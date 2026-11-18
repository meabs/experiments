#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    # Priority suffix
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += "".join(" #{}".format(t) for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def err(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def snapshot(data):
    """Save a snapshot of current state for undo."""
    data["history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })


def do_add(args):
    """Handle the 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                err("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                err("Invalid priority: {}".format(priority))
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                err("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                err("--due requires a value")
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                err("Invalid date: {}".format(due_str))
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        err("Missing task title")

    title = " ".join(title_parts)
    data = load_data()

    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    snapshot(data)

    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print("Added {}".format(task_id))


def do_list(args):
    """Handle the 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    data = load_data()
    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and date.fromisoformat(t["due"]) < today
        ]

    if not tasks:
        has_filters = any(a in ("--sort", "--tag", "--overdue", "--today")
                          for a in args)
        if not has_filters:
            print("No tasks")
        return

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (
            priority_order.get(t.get("priority", "medium"), 1),
            t["id"]))

    for task in tasks:
        print(task_line(task))


def do_done(args):
    """Handle the 'done' command."""
    if not args:
        err("Missing task ID")
    task_id = int(args[0])
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        err("No such task: {}".format(task_id))

    snapshot(data)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def do_delete(args):
    """Handle the 'delete' command."""
    if not args:
        err("Missing task ID")
    task_id = int(args[0])
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        err("No such task: {}".format(task_id))

    snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def do_edit(args):
    """Handle the 'edit' command."""
    if not args:
        err("Missing task ID")
    task_id = int(args[0])
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        err("No such task: {}".format(task_id))

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        err("Missing --title")

    snapshot(data)
    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def do_search(args):
    """Handle the 'search' command."""
    if not args:
        err("Missing search text")

    search_text = " ".join(args).lower()
    data = load_data()
    tasks = [t for t in data["tasks"] if search_text in t["title"].lower()]

    if not tasks:
        print("No matches")
        return

    for task in tasks:
        print(task_line(task))


def do_export(args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        err("--format is required")
    if fmt not in ("json", "csv"):
        err("Invalid format: {}".format(fmt))

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        out = []
        for t in tasks:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(out, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due") or "",
            ])
        print(output.getvalue(), end="")


def do_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def do_undo(args):
    """Handle the 'undo' command."""
    data = load_data()
    if not data["history"]:
        err("Nothing to undo")

    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


COMMANDS = {
    "add": do_add,
    "list": do_list,
    "done": do_done,
    "delete": do_delete,
    "edit": do_edit,
    "search": do_search,
    "export": do_export,
    "stats": do_stats,
    "undo": do_undo,
}


def main():
    if len(sys.argv) < 2:
        err("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        err("Unknown command: {}".format(command))

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
