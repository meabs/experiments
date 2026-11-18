#!/usr/bin/env python3
"""A command-line task manager using only the Python 3 standard library."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    """Load tasks from the data file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_tasks(tasks):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def load_history():
    """Load undo history from the history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_history(history):
    """Save undo history to the history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_next_id(tasks):
    """Get the next available task id."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task_line(task):
    """Format a task as a display line."""
    done_marker = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {done_marker} {task["title"]}'
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def push_undo(tasks):
    """Push current task state onto undo history."""
    history = load_history()
    history.append(list(tasks))  # shallow copy of list is enough since we store full state
    # Keep only last 100 states
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def undo(args):
    """Revert to the previous state."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = history.pop()
    save_history(history)
    save_tasks(prev_state)
    print("Undone")


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Handle the 'add' command."""
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            i += 1
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            i += 1
            tags.append(args[i])
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            i += 1
            due_value = args[i]
            # Validate date
            try:
                datetime.strptime(due_value, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_value}")
            due = due_value
        else:
            title_parts.append(arg)
        i += 1

    title = " ".join(title_parts)
    if not title:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    tasks = load_tasks()
    push_undo(tasks)
    new_id = get_next_id(tasks)
    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {new_id}")


def cmd_list(args):
    """Handle the 'list' command."""
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    today = date.today()

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            i += 1
            sort_by = args[i]
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            i += 1
            tag_filter = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            i += 1
            today_str = args[i]
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
        i += 1

    tasks = load_tasks()

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    # Filter overdue: open tasks whose due date is before today
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t["due"]:
                due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                if due_date < today:
                    filtered.append(t)
        tasks = filtered

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(format_task_line(t))


def cmd_done(args):
    """Handle the 'done' command."""
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")

    tasks = load_tasks()
    push_undo(tasks)
    found = False
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")

    tasks = load_tasks()
    push_undo(tasks)
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(new_tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")

    # Find --title flag
    title_idx = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_idx = i
            break

    if title_idx is None or title_idx + 1 >= len(args):
        error("Usage: edit ID --title NEW TITLE")

    new_title_parts = args[title_idx + 1:]
    new_title = " ".join(new_title_parts)

    tasks = load_tasks()
    push_undo(tasks)
    found = False
    for t in tasks:
        if t["id"] == task_id:
            t["title"] = new_title
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        error("Usage: search TEXT")

    query = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task_line(t))


def cmd_export(args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            i += 1
            fmt = args[i]
        i += 1

    if fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")

    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            done_str = "true" if t["done"] else "false"
            print(f'{t["id"]},{t["title"]},{done_str},{t["priority"]},{tags_str},{due_str}')


def cmd_stats(args):
    """Handle the 'stats' command."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

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
        "undo": undo,
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args)


if __name__ == "__main__":
    main()
