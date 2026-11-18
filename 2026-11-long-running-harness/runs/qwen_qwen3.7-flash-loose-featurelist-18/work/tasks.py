#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_data():
    """Load tasks and next_id from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and next_id to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    """Load undo history from undo.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(history):
    """Save undo history to undo.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def append_undo(snapshot):
    """Append a snapshot of the current state to undo history."""
    history = load_undo()
    history.append(snapshot)
    save_undo(history)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task for display."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
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
                error("Invalid date: ")
            due_str = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
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
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    append_undo({"tasks": data["tasks"], "next_id": data["next_id"]})
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_data()
    tasks = list(data["tasks"])  # copy to avoid mutating original

    # Parse flags
    sort_priority = False
    filter_tag = None
    overdue = False
    today_date = date.today()

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            sort_val = args[i + 1]
            if sort_val != "priority":
                error(f"Unknown sort option: {sort_val}")
            sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing --today value")
            today_str = args[i + 1]
            try:
                today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filtering: only open tasks whose due date is before today
    if overdue:
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_date.isoformat()
        ]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
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

    task["done"] = True
    save_data(data)
    append_undo({"tasks": data["tasks"], "next_id": data["next_id"]})
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

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    append_undo({"tasks": data["tasks"], "next_id": data["next_id"]})
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
    i = 1  # skip task id
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            new_title = " ".join(args[i + 1 :])
            break
        else:
            error(f"Unknown edit option: {args[i]}")

    if new_title is None:
        error("Missing --title option")

    task["title"] = new_title
    save_data(data)
    append_undo({"tasks": data["tasks"], "next_id": data["next_id"]})
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    data = load_data()
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    matches = []
    for task in data["tasks"]:
        if query in task["title"].lower():
            matches.append(task)

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
            error(f"Unknown option: {args[i]}")

    if fmt is None:
        error("Missing --format option")

    if fmt == "json":
        output = []
        for task in data["tasks"]:
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in data["tasks"]:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due", "")
            done_str = "true" if task["done"] else "false"
            print(f'{task["id"]},{task["title"]},{done_str},{task.get("priority", "medium")},{tags_str},{due_str}')
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    history = load_undo()
    if not history:
        error("Nothing to undo")

    previous = history.pop()
    save_undo(history)
    save_data(previous)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: tasks.py <command> [args]")

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

    if command not in commands:
        error(f"Unknown command: {command}")

    commands[command](args)


if __name__ == "__main__":
    main()
