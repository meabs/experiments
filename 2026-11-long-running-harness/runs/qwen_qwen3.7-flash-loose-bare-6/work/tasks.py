#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def validate_date(value):
    """Validate a YYYY-MM-DD date string."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_task_line(task):
    """Format a task into its display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
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
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("Missing value for --priority")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing value for --tag")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("Missing value for --due")
            due = args[i]
            if not validate_date(due):
                error(f"Invalid date: {due}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["next_id"] += 1
    task_key = str(task_id)

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][task_key] = task

    # Save undo snapshot
    data["history"].append({
        "type": "add",
        "task_id": task_id,
        "prev_next_id": data["next_id"] - 1,
    })
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """List tasks."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                error("Missing value for --sort")
            sort_key = args[i]
            if sort_key == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {sort_key}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing value for --tag")
            tag_filter = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                error("Missing value for --today")
            today_str = args[i]
        else:
            error(f"Unknown argument: {arg}")
        i += 1

    today = today_str if today_str else date.today().isoformat()

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    # Filter by tag if specified
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter: only open tasks with due date before today
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if not tasks:
        if overdue or tag_filter:
            pass
        else:
            print("No tasks")
            return

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    task_key = str(task_id)
    if task_key not in data["tasks"]:
        error(f"No such task: {task_id}")

    task = data["tasks"][task_key]
    task["done"] = True

    # Save undo snapshot
    data["history"].append({
        "type": "done",
        "task_id": task_id,
        "prev_done": False,
    })
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    task_key = str(task_id)
    if task_key not in data["tasks"]:
        error(f"No such task: {task_id}")

    task = data["tasks"].pop(task_key)

    # Save undo snapshot
    data["history"].append({
        "type": "delete",
        "task_id": task_id,
        "task": task,
    })
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    task_key = str(task_id)
    if task_key not in data["tasks"]:
        error(f"No such task: {task_id}")

    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                error("Missing value for --title")
            title_parts = args[i:]
            break
        else:
            error(f"Unknown argument: {args[i]}")
        i += 1

    if not title_parts:
        error("Missing title")

    new_title = " ".join(title_parts)
    old_title = data["tasks"][task_key]["title"]
    data["tasks"][task_key]["title"] = new_title

    # Save undo snapshot
    data["history"].append({
        "type": "edit",
        "task_id": task_id,
        "prev_title": old_title,
    })
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("Missing value for --format")
            fmt = args[i]
        else:
            error(f"Unknown argument: {args[i]}")
        i += 1

    if fmt is None:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            done_str = "true" if task["done"] else "false"
            print(f'{task["id"]},{task["title"]},{done_str},{task.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(args, data):
    """Show task statistics."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the most recent mutating command."""
    if not data["history"]:
        error("Nothing to undo")

    entry = data["history"].pop()
    task_id = entry["task_id"]
    task_key = str(task_id)

    if entry["type"] == "add":
        if task_key in data["tasks"]:
            del data["tasks"][task_key]
        data["next_id"] = entry["prev_next_id"]
    elif entry["type"] == "done":
        if task_key in data["tasks"]:
            data["tasks"][task_key]["done"] = entry["prev_done"]
    elif entry["type"] == "delete":
        data["tasks"][task_key] = entry["task"]
    elif entry["type"] == "edit":
        if task_key in data["tasks"]:
            data["tasks"][task_key]["title"] = entry["prev_title"]

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
        error("Usage: tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
