#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from JSON file, or return initial state."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1, "undo_history": []}


def save_data(data):
    """Save tasks to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix (medium shows nothing)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    if task.get("tags"):
        line += " " + " ".join(f"#{tag}" for tag in task["tags"])
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def task_exists(data, task_id):
    """Check if a task exists."""
    for t in data["tasks"]:
        if t["id"] == task_id:
            return True
    return False


def find_task(data, task_id):
    """Find a task by id, or error if not found."""
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    error(f"No such task: {task_id}")


def push_undo(data):
    """Push current state onto undo history."""
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["undo_history"].append(snapshot)


def cmd_add(args, data):
    """Add a new task."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
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
            due_str = args[i + 1]
            try:
                parsed = datetime.strptime(due_str, "%Y-%m-%d").date()
                due = parsed.isoformat()
            except ValueError:
                error(f"Invalid date: {due_str}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    push_undo(data)

    task_id = data["next_id"]
    data["next_id"] += 1

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """List tasks with optional filtering and sorting."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_key = args[i + 1]
            if sort_key == "priority":
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
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    # Determine today's date
    if today_str:
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
    else:
        today = date.today()

    today_iso = today.isoformat()

    # Start with all tasks
    filtered = list(data["tasks"])

    # Filter by tag
    if filter_tag is not None:
        filtered = [t for t in filtered if filter_tag in t.get("tags", [])]

    # Filter by overdue
    if overdue:
        filtered = [
            t for t in filtered
            if not t["done"]
            and t.get("due")
            and t["due"] < today_iso
        ]

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
    else:
        for t in filtered:
            print(format_task(t))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        error("Missing task id")
    task_id = int(args[0])
    if not task_exists(data, task_id):
        error(f"No such task: {task_id}")

    push_undo(data)

    task = find_task(data, task_id)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        error("Missing task id")
    task_id = int(args[0])
    if not task_exists(data, task_id):
        error(f"No such task: {task_id}")

    push_undo(data)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task title."""
    if not args:
        error("Missing task id")
    task_id = int(args[0])
    if not task_exists(data, task_id):
        error(f"No such task: {task_id}")

    title_idx = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            title_idx = i
            break
        i += 1

    if title_idx is None:
        error("Missing --title flag")

    new_title_parts = args[title_idx + 1:]
    if not new_title_parts:
        error("Missing new title")

    new_title = " ".join(new_title_parts)

    push_undo(data)

    task = find_task(data, task_id)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title substring (case-insensitive)."""
    if not args:
        error("Missing search text")

    search_text = " ".join(args).lower()

    matches = []
    for t in data["tasks"]:
        if search_text in t["title"].lower():
            matches.append(t)

    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task(t))


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

    if fmt not in ("json", "csv"):
        error("Must specify --format json or --format csv")

    sorted_tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_list = []
        for t in sorted_tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_list, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in sorted_tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Show task statistics."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    if not data["undo_history"]:
        error("Nothing to undo")

    snapshot = data["undo_history"].pop()
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_data()

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

    commands[command](args, data)


if __name__ == "__main__":
    main()
