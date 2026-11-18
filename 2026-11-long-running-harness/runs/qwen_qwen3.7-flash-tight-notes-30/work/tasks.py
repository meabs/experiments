#!/usr/bin/env python3
"""A command-line task manager."""

import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"tasks": [], "next_id": 1, "undo_history": []}


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]

    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")
    # medium shows no suffix

    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        parts.append(f"#{tag}")

    # Due date suffix
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")

    return " ".join(parts)


def push_undo(data):
    """Push current state onto undo history."""
    data["undo_history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })


def find_task(data, task_id):
    """Find a task by id, or error if not found."""
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    error(f"No such task: {task_id}")


def parse_add(args):
    """Handle 'add' command."""
    if not args:
        error("Usage: add TITLE [--priority PRIORITY] [--tag TAG]... [--due DATE]")

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
            # Validate date
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    title = " ".join(title_parts)
    if not title:
        error("Usage: add TITLE [--priority PRIORITY] [--tag TAG]... [--due DATE]")

    data = load_data()
    push_undo(data)

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


def parse_list(args):
    """Handle 'list' command."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue and today is None:
        today = date.today().isoformat()

    data = load_data()
    tasks = list(data["tasks"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue and today:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def parse_done(args):
    """Handle 'done' command."""
    if not args:
        error("Usage: done ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    data = load_data()
    task = find_task(data, task_id)
    push_undo(data)

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def parse_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Usage: delete ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    data = load_data()
    task = find_task(data, task_id)
    push_undo(data)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def parse_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        error("Usage: edit ID --title NEW TITLE")

    data = load_data()
    task = find_task(data, task_id)
    push_undo(data)

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def parse_search(args):
    """Handle 'search' command."""
    if not args:
        error("Usage: search TEXT")

    text = " ".join(args).lower()
    data = load_data()

    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def parse_export(args):
    """Handle 'export' command."""
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
        error("Usage: export --format json|csv")

    if fmt not in ("json", "csv"):
        error(f"Invalid format: {fmt}")

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for task in tasks:
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
        for task in tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{done_str},{task.get('priority', 'medium')},{tags_str},{due_str}")


def parse_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def parse_undo(args):
    """Handle 'undo' command."""
    data = load_data()
    if not data["undo_history"]:
        error("Nothing to undo")

    prev = data["undo_history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "add": parse_add,
        "list": parse_list,
        "done": parse_done,
        "delete": parse_delete,
        "edit": parse_edit,
        "search": parse_search,
        "export": parse_export,
        "stats": parse_stats,
        "undo": parse_undo,
    }

    if command not in commands:
        error(f"Unknown command: {command}")

    commands[command](args)


if __name__ == "__main__":
    main()
