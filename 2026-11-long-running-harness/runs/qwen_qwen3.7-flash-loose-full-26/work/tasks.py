#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


TASKS_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the JSON file."""
    if not os.path.exists(TASKS_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(TASKS_FILE, "r") as f:
        data = json.load(f)
    # JSON keys are always strings; convert task IDs back to int
    if isinstance(data.get("tasks"), dict):
        data["tasks"] = {int(k): v for k, v in data["tasks"].items()}
    return data


def save_data(data):
    """Save tasks and undo history to the JSON file."""
    with open(TASKS_FILE, "w") as f:
        json.dump(_convert_keys_to_str(data), f, indent=2)


def _convert_keys_to_str(obj):
    """Convert all integer keys to strings for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): _convert_keys_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_keys_to_str(item) for item in obj]
    else:
        return obj


def error(msg):
    """Print error to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    """Format a task for display."""
    done_mark = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_mark} {task['title']}"
    # priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium shows no suffix
    # tags suffix
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    # due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_data()
    # Parse args for title and options
    title_parts = []
    priority = None
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
                error("Missing due date")
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
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(title_parts)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }

    # Save state before mutation for undo
    data["history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"][task["id"]] = task
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_data()
    tasks = list(data["tasks"].values())

    # Parse args
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_by = args[i + 1]
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
                error("--today requires a date value")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    if not tasks:
        print("No tasks")
        return

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue (only open tasks due before today)
    if overdue:
        if today_str:
            today_val = today_str
        else:
            today_val = date.today().strftime("%Y-%m-%d")
        new_tasks = []
        for t in tasks:
            if not t["done"] and t.get("due"):
                if t["due"] < today_val:
                    new_tasks.append(t)
        tasks = new_tasks

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    elif sort_by:
        error(f"Unknown sort option: {sort_by}")
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(format_task_line(t))


def cmd_done(args):
    """Handle the 'done' command."""
    data = load_data()
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    data = load_data()
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })

    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    data = load_data()
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Parse --title
    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            # Collect remaining args as title
            title_parts = args[i:]
            break
        else:
            i += 1

    if not title_parts:
        error("Usage: edit ID --title NEW TITLE")

    new_title = " ".join(title_parts)

    # Save state for undo
    data["history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    data = load_data()
    if not args:
        error("Usage: search TEXT")

    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task_line(t))


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

    if not fmt:
        error("Usage: export --format json|csv")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_list = []
        for t in tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_list))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")

    previous = data["history"].pop()
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
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
