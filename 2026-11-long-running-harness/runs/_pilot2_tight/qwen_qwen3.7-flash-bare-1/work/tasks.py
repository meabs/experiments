#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from JSON file, or return initial state."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "history": []}


def save_data(data):
    """Save tasks data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task for display in list/search output."""
    check = "x" if task["done"] else " "
    line = f"{task['id']} [{check}] {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def save_history(data):
    """Save a snapshot of current state into history."""
    data["history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })


def cmd_add(args):
    """Handle 'add' command."""
    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None
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
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        error("Missing task title")

    new_id = data["next_id"]
    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][str(new_id)] = task
    data["next_id"] = new_id + 1

    # Save history snapshot BEFORE mutating
    save_history(data)

    save_data(data)
    print(f"Added {new_id}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = list(data["tasks"].values())

    # Parse options
    show_tag = None
    sort_priority = False
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--tag" and i + 1 < len(args):
            show_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        elif args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort_priority = True
            i += 2
        else:
            i += 1

    if overdue:
        if today_str is None:
            today_str = date.today().isoformat()
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
        filtered = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]
    else:
        filtered = tasks

    if show_tag is not None:
        filtered = [t for t in filtered if show_tag in t.get("tags", [])]

    if sort_priority:
        filtered.sort(key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(format_task(task))


def cmd_done(args):
    """Handle 'done' command."""
    data = load_data()
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save history snapshot BEFORE mutating
    save_history(data)

    data["tasks"][key]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    data = load_data()
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save history snapshot BEFORE mutating
    save_history(data)

    del data["tasks"][key]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    data = load_data()
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Parse --title option; rest after --title is the new title
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            # Collect all remaining args as title parts
            title_parts = []
            i += 1
            while i < len(args):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        error("Missing --title option")

    # Save history snapshot BEFORE mutating
    save_history(data)

    data["tasks"][key]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    data = load_data()
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format option")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

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
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(list(tasks))
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    """Handle 'undo' command."""
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
