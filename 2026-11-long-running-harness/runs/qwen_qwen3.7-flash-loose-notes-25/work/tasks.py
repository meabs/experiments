#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error to stderr and exit with code 1."""
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
    # medium has no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def snapshot(data):
    """Create a deep copy of the state for undo."""
    return json.loads(json.dumps(data))


def cmd_add(args):
    """Add a new task."""
    data = load_data()

    priority = "medium"
    tags = []
    due = None

    # Parse args for flags
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due_str = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            positional.append(args[i])
            i += 1

    title = " ".join(positional)
    if not title:
        error("No title provided")

    # Save snapshot for undo
    data["undo_history"].append(snapshot(data))

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """List tasks."""
    data = load_data()
    tasks = data["tasks"]

    sort_priority = False
    tag_filter = None
    overdue = False
    today_val = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today_val = args[i + 1]
            i += 2
        else:
            i += 1

    # Apply tag filter
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    # Apply overdue filter
    if overdue:
        if today_val:
            try:
                today = datetime.strptime(today_val, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_val}")
        else:
            today = date.today()
        today_str = str(today)
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_str]

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()

    if not args:
        error("No ID provided")

    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)

    if task is None:
        error(f"No such task: {task_id}")

    data["undo_history"].append(snapshot(data))
    task["done"] = True

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    data = load_data()

    if not args:
        error("No ID provided")

    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)

    if task is None:
        error(f"No such task: {task_id}")

    data["undo_history"].append(snapshot(data))
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task."""
    data = load_data()

    if not args:
        error("No ID provided")

    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)

    if task is None:
        error(f"No such task: {task_id}")

    # Parse --title
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            # Collect all remaining args as title parts
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        error("--title required")

    data["undo_history"].append(snapshot(data))
    task["title"] = new_title

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by text."""
    data = load_data()

    if not args:
        error("No search text provided")

    search_text = " ".join(args).lower()

    matches = [t for t in data["tasks"] if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Export tasks."""
    data = load_data()

    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        error(f"Invalid format: {fmt}")

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
        print(json.dumps(export_tasks, indent=2))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args):
    """Show task statistics."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()

    if not data["undo_history"]:
        error("Nothing to undo")

    previous_state = data["undo_history"].pop()
    # Restore full state including undo_history from the snapshot
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
    data["undo_history"] = previous_state["undo_history"]

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

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
