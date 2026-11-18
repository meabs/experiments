#!/usr/bin/env python3
"""A command-line task manager. Python 3 standard library only."""

import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task into its display string."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{tag}" for tag in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def snapshot(data):
    """Save current state for undo."""
    data["history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_data()
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except (ValueError, TypeError):
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    task = {
        "id": data["next_id"],
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
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_data()
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return

    sort_priority = False
    tag_filter = None
    overdue_mode = False
    today_str = None
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue_mode = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing --today value")
            today_str = args[i + 1]
            try:
                today = date.fromisoformat(today_str)
            except (ValueError, TypeError):
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            i += 1

    if today is None:
        today = date.today()

    filtered = list(tasks)

    # Tag filter
    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t["tags"]]

    # Overdue filter: open tasks whose due date is before today
    if overdue_mode:
        filtered = [
            t for t in filtered
            if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today
        ]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    for task in filtered:
        print(format_task(task))


def cmd_done(args):
    """Handle the 'done' command."""
    data = load_data()
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    snapshot(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    data = load_data()
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    data = load_data()
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing new title value")
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        error("Missing --title option")

    snapshot(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    data = load_data()
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()

    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Handle the 'export' command."""
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format option")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_list = []
        for t in tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_list))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] or "",
            ])
        print(output.getvalue(), end="")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")
    previous = json.loads(data["history"].pop())
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

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

    handler = commands.get(command)
    if handler is None:
        error(f"Unknown command: {command}")

    handler(args)


if __name__ == "__main__":
    main()
