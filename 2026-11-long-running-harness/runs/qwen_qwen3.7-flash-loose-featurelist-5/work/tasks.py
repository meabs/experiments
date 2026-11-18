#!/usr/bin/env python3
"""A command-line task manager."""

import copy
import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from the JSON data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks to the JSON data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    """Load undo history from the JSON history file."""
    history_file = "undo_history.json"
    if not os.path.exists(history_file):
        return []
    with open(history_file, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to the JSON history file."""
    history_file = "undo_history.json"
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"

    # Priority suffix (feature 5)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix

    # Tags suffix (feature 6)
    for tag in task.get("tags", []):
        line += f" #{tag}"

    # Due date suffix (feature 7)
    if task.get("due"):
        line += f" due:{task['due']}"

    return line


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_data()
    history = load_history()

    title = None
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
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Invalid date: ")
            due = args[i + 1]
            # Validate date
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if month < 1 or month > 12:
                    raise ValueError
                import calendar
                max_day = calendar.monthrange(year, month)[1]
                if day < 1 or day > max_day:
                    raise ValueError
            except (ValueError, IndexError):
                error(f"Invalid date: {due}")
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        error("Missing task title")

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Save previous state for undo (deep copy via json roundtrip)
    history.append({"type": "add", "data": json.loads(json.dumps(data))})

    data["tasks"].append(task)
    data["next_id"] += 1

    save_data(data)
    save_history(history)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_data()
    tasks = list(data["tasks"])  # copy to avoid mutation issues

    sort_mode = None
    filter_tag = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date value")
            today = args[i + 1]
            i += 2
        else:
            i += 1

    import datetime

    if today is None:
        today = datetime.date.today().isoformat()

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    # Default sort is by id

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Handle the 'done' command."""
    data = load_data()
    history = load_history()

    try:
        task_id = int(args[0])
    except (ValueError, IndexError):
        error("Usage: done ID")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save previous state for undo (deep copy)
    history.append({"type": "done", "data": json.loads(json.dumps(data))})
    task["done"] = True

    save_data(data)
    save_history(history)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    data = load_data()
    history = load_history()

    try:
        task_id = int(args[0])
    except (ValueError, IndexError):
        error("Usage: delete ID")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save previous state for undo (deep copy)
    history.append({"type": "delete", "data": json.loads(json.dumps(data))})
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    save_data(data)
    save_history(history)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    data = load_data()
    history = load_history()

    try:
        task_id = int(args[0])
    except (ValueError, IndexError):
        error("Usage: edit ID --title NEW TITLE")

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
                error("--title requires a value")
            # Collect all remaining arguments as the new title
            new_title = " ".join(args[i+1:])
            break
        else:
            i += 1

    if new_title is None:
        error("--title is required")

    # Save previous state for undo (deep copy)
    history.append({"type": "edit", "data": json.loads(json.dumps(data))})
    task["title"] = new_title

    save_data(data)
    save_history(history)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    data = load_data()
    text = " ".join(args).lower()

    matches = []
    for task in data["tasks"]:
        if text in task["title"].lower():
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
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("--format is required")

    if fmt == "json":
        export_data = []
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
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
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{done_str},{task.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    history = load_history()

    if not history:
        error("Nothing to undo")

    last_action = history.pop()
    save_history(history)

    data = last_action["data"]
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
