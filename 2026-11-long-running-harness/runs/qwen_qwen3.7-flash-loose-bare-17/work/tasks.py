#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    """Load tasks from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    """Save tasks to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    """Load undo history from tasks_undo.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to tasks_undo.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    """Push current state onto undo history."""
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_history(history)


def undo_last(args=None):
    """Revert the most recent mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = history.pop()
    save_history(history)
    save_tasks(prev["tasks"], prev["next_id"])
    print("Undone")


def format_task_line(task):
    """Format a task for display."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
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


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Add a new task."""
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            val = args[i + 1]
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {val}")
            due = val
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        error("Missing task title")

    tasks, next_id = load_tasks()
    push_history(tasks, next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    """List tasks."""
    tasks, _ = load_tasks()
    sort_priority = False
    filter_tag = None
    show_overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            show_overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filter
    if show_overdue:
        if today_str is not None:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
        else:
            today = date.today()
        today_str_val = today.strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str_val]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    tasks, next_id = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        error(f"No such task: {task_id}")

    push_history(tasks, next_id)
    found["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    tasks, next_id = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        error(f"No such task: {task_id}")

    push_history(tasks, next_id)
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    tasks, next_id = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        error(f"No such task: {task_id}")

    new_title = None

    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            new_title = args[i + 1]
            i += 2
        else:
            i += 1

    if new_title is None:
        error("--title is required")

    push_history(tasks, next_id)
    found["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()

    tasks, _ = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
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
        error("--format is required (json or csv)")

    tasks, _ = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{str(t['done']).lower()},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    """Show task statistics."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": undo_last,
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
