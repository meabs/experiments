#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium has no suffix
    # Tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args, data):
    """Add a new task."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
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
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("No title provided")

    title = " ".join(title_parts)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    data["history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

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

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        today = date.fromisoformat(today_str) if today_str else date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today.isoformat()
        ]

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if not task:
        error(f"No such task: {task_id}")

    data["history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if not task:
        error(f"No such task: {task_id}")

    data["history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if not task:
        error(f"No such task: {task_id}")

    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            while i < len(args):
                if args[i].startswith("--"):
                    break
                new_title_parts.append(args[i])
                i += 1
        else:
            i += 1

    if not new_title_parts:
        error("--title is required")

    new_title = " ".join(new_title_parts)

    data["history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title (case-insensitive)."""
    if not args:
        error("Usage: search TEXT")

    query = " ".join(args).lower()

    matches = [t for t in data["tasks"] if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def cmd_export(args, data):
    """Export tasks in json or csv format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    if not fmt:
        error("--format is required")

    if fmt == "json":
        export_json(data)
    elif fmt == "csv":
        export_csv(data)
    else:
        error(f"Unknown format: {fmt}")


def export_json(data):
    """Export tasks as JSON array."""
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    result = []
    for t in tasks:
        result.append({
            "id": t["id"],
            "title": t["title"],
            "done": t["done"],
            "priority": t.get("priority", "medium"),
            "tags": t.get("tags", []),
            "due": t.get("due", None),
        })
    print(json.dumps(result))


def export_csv(data):
    """Export tasks as CSV."""
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    print("id,title,done,priority,tags,due")
    for t in tasks:
        tags_str = ";".join(t.get("tags", []))
        due_str = t.get("due", "") or ""
        print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Print task statistics."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total_count = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args, data):
    """Undo the most recent mutating command."""
    if not data["history"]:
        error("Nothing to undo")

    snapshot = data["history"].pop()
    state = json.loads(snapshot)
    data["tasks"] = state["tasks"]
    data["next_id"] = state["next_id"]
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