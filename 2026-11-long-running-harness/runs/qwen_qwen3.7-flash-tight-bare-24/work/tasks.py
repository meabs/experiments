#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "history": []}
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    tasks = {}
    for k, v in raw.get("tasks", {}).items():
        tasks[int(k)] = copy.deepcopy(v)
    raw["tasks"] = tasks
    raw["history"] = [copy.deepcopy(h) for h in raw.get("history", [])]
    return raw


def save_data(data):
    """Save tasks and history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def next_id(tasks):
    """Return the next available task id."""
    if not tasks:
        return 1
    return max(tasks.keys()) + 1


def format_task(task):
    """Format a task for display."""
    line = f"{task['id']} [{'x' if task['done'] else ' '}] {task['title']}"
    # Priority suffix (high/low only; medium has no suffix)
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def error(msg):
    """Print error message to stderr and exit."""
    print(msg, file=sys.stderr)
    sys.exit(1)


# ── Commands ────────────────────────────────────────────────────────

def cmd_add(args, data):
    """Add a new task."""
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None or title.strip() == "":
        error("Missing task title")

    tasks = data["tasks"]
    nid = next_id(tasks)
    tasks[nid] = {
        "id": nid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Snapshot state before mutation for undo
    data["history"].append(copy.deepcopy(tasks))
    save_data(data)
    print(f"Added {nid}")


def cmd_list(args, data):
    """List tasks."""
    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return

    sort_mode = None
    tag_filter = None
    overdue_today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue_today = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            overdue_today = args[i + 1]
            try:
                date.fromisoformat(overdue_today)
            except ValueError:
                error(f"Invalid date: {overdue_today}")
            i += 2
        else:
            i += 1

    task_list = sorted(tasks.values(), key=lambda t: t["id"])

    # Filter by tag
    if tag_filter:
        task_list = [t for t in task_list if tag_filter in t.get("tags", [])]

    # Filter overdue
    if overdue_today is True:
        today_str = date.today().isoformat()
        task_list = [
            t for t in task_list
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]
    elif isinstance(overdue_today, str):
        task_list = [
            t for t in task_list
            if not t["done"] and t.get("due") and t["due"] < overdue_today
        ]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        task_list.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not task_list:
        print("No tasks")
        return

    for t in task_list:
        print(format_task(t))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        error("Missing task ID")
    tid = int(args[0])
    tasks = data["tasks"]
    if tid not in tasks:
        error(f"No such task: {tid}")

    data["history"].append(copy.deepcopy(tasks))
    tasks[tid]["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        error("Missing task ID")
    tid = int(args[0])
    tasks = data["tasks"]
    if tid not in tasks:
        error(f"No such task: {tid}")

    data["history"].append(copy.deepcopy(tasks))
    del tasks[tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        error("Missing task ID")
    tid = int(args[0])
    tasks = data["tasks"]
    if tid not in tasks:
        error(f"No such task: {tid}")

    new_title = None
    i = 1  # skip the ID
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1

    if new_title is None or new_title.strip() == "":
        error("Missing new title")

    data["history"].append(copy.deepcopy(tasks))
    tasks[tid]["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Search tasks by title substring (case-insensitive)."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    tasks = data["tasks"]
    results = [
        t for t in tasks.values()
        if query in t["title"].lower()
    ]
    results.sort(key=lambda t: t["id"])
    if not results:
        print("No matches")
        return
    for t in results:
        print(format_task(t))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        error(f"Invalid format: {fmt}")

    tasks = data["tasks"]
    task_list = sorted(tasks.values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in task_list:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in task_list:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due") or "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args, data):
    """Print open/done/total counts."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the most recent mutating command."""
    if not data["history"]:
        error("Nothing to undo")
    prev_state = data["history"].pop()
    data["tasks"] = prev_state
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
    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](sys.argv[2:], data)


if __name__ == "__main__":
    main()
