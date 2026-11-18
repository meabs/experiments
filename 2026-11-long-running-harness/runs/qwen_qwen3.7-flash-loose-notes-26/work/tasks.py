#!/usr/bin/env python3
"""Command-line task manager using only Python 3 standard library."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    for tag in task["tags"]:
        line += f" #{tag}"
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    """Add a new task."""
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    # Save snapshot for undo before mutation
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    """List tasks with optional filters and sorting."""
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
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    tasks = list(data["tasks"])

    if overdue:
        if today_str is None:
            today = date.today().isoformat()
        else:
            today = today_str
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks and not overdue and not tag_filter:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Save snapshot for undo
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))
    task["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Save snapshot for undo
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            new_title = args[i + 1]
            i += 2
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    # Save snapshot for undo
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))
    task["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Search tasks by title (case-insensitive)."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    # Already in id order since tasks are appended in id order
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Print task statistics."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the most recent mutating command."""
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    snapshot = json.loads(data["undo_history"].pop())
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
