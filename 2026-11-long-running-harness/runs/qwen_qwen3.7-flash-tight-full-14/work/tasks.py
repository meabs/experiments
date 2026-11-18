#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = ".tasks_undo.json"


def load_data():
    """Load tasks and next_id from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, KeyError):
        return {"tasks": [], "next_id": 1}


def save_data(data):
    """Save tasks and next_id to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    """Load undo history from undo file."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo(history):
    """Save undo history to undo file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def format_task_line(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # tags suffix
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    # due date suffix
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
    positional = []
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            # Validate date
            try:
                parts = due.split("-")
                if len(parts) != 3:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, TypeError):
                error(f"Invalid date: {due}")
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if not positional:
        error("Missing title")

    title = " ".join(positional)

    data = load_data()
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] = task_id + 1
    save_data(data)

    print(f"Added {task_id}")


def cmd_list(args):
    """List tasks with optional filtering and sorting."""
    sort_mode = None
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    if today_str:
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
    else:
        today = date.today()

    data = load_data()
    tasks = data["tasks"]

    # Filter by tag if specified
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue: only open tasks with due date before today
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = date.fromisoformat(t["due"])
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (
            priority_order.get(t.get("priority", "medium"), 1),
            t["id"]
        ))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    found = None
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        error(f"No such task: {task_id}")

    found["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    found = None
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        error(f"No such task: {task_id}")

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    found = None
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        error(f"No such task: {task_id}")

    # Find --title flag
    i = 1
    new_title_parts = []
    while i < len(args):
        if args[i] == "--title":
            i += 1
            # Collect remaining args as title
            new_title_parts = args[i:]
            break
        i += 1

    if not new_title_parts:
        error("Missing --title")

    new_title = " ".join(new_title_parts)
    found["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title substring."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    data = load_data()
    tasks = data["tasks"]

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
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
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
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')


def cmd_stats(args):
    """Show task statistics."""
    data = load_data()
    tasks = data["tasks"]
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    history = load_undo()
    if not history:
        error("Nothing to undo")

    # Pop the last state
    previous_state = history.pop()
    save_undo(history)

    # Restore the state
    data = previous_state
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

    # For mutating commands, we need to save state before mutation for undo
    if command in ("add", "done", "delete", "edit"):
        # Save current state for potential undo
        history = load_undo()
        current_data = load_data()
        history.append(current_data)
        save_undo(history)

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
