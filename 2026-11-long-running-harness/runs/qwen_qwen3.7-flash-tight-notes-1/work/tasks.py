#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
import copy
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


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
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def snapshot(data):
    """Create a deep copy of the current state for undo."""
    return copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]})


def cmd_add(args, data):
    """Add a new task."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    raw_args = list(args)

    # Parse flags first
    while i < len(raw_args):
        arg = raw_args[i]
        if arg == "--priority":
            if i + 1 >= len(raw_args):
                error("Invalid priority: ")
            val = raw_args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(raw_args):
                error("--tag requires a value")
            tags.append(raw_args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(raw_args):
                error("--due requires a value")
            val = raw_args[i + 1]
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {val}")
            due = val
            i += 2
        else:
            title_parts.append(arg)
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

    # Save snapshot before mutation
    data["history"].append(snapshot(data))
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    """List tasks with optional filters and sorting."""
    sort_mode = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_mode = args[i + 1]
            if sort_mode != "priority":
                error(f"Unknown sort option: {sort_mode}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            error(f"Unknown option: {arg}")

    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    # Overdue filter: open tasks whose due date is before today
    if overdue:
        today = today_str if today_str else date.today().isoformat()
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        tasks = [
            t for t in tasks
            if not t["done"] and t["due"] and datetime.strptime(t["due"], "%Y-%m-%d").date() < today_date
        ]

    # Sort by priority if requested
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
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

    data["history"].append(snapshot(data))
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
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

    data["history"].append(snapshot(data))
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
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

    # Parse --title flag
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            i += 1
            # Collect remaining args as title parts
            while i < len(args):
                new_title_parts.append(args[i])
                i += 1
        else:
            error(f"Unknown option: {args[i]}")

    if not new_title_parts:
        error("--title requires a value")

    new_title = " ".join(new_title_parts)

    data["history"].append(snapshot(data))
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    results = [t for t in data["tasks"] if query in t["title"].lower()]
    results.sort(key=lambda t: t["id"])

    if not results:
        print("No matches")
        return

    for task in results:
        print(task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                error(f"Unknown format: {fmt}")
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    if fmt is None:
        error("--format is required")

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
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Print statistics about tasks."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total_count = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    if not data["history"]:
        error("Nothing to undo")

    previous_state = data["history"].pop()
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
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
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
