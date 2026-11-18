#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    """Load tasks and next_id from data file."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_data(tasks, next_id):
    """Save tasks and next_id to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    """Load undo history from history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def do_add(args):
    """Handle the 'add' command."""
    tasks, next_id = load_data()
    history = load_history()

    title_parts = []
    priority = None
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
                date.fromisoformat(due_str)
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("add requires a title")

    title = " ".join(title_parts)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }

    tasks.append(task)
    new_next_id = next_id + 1

    # Save state for undo
    prev_state = {"tasks": tasks[:-1], "next_id": next_id}
    history.append(prev_state)
    save_history(history)

    save_data(tasks, new_next_id)
    print(f"Added {task['id']}")


def do_list(args):
    """Handle the 'list' command."""
    tasks, next_id = load_data()

    sort_mode = None
    tag_filter = None
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
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date value")
            today = args[i + 1]
            try:
                date.fromisoformat(today)
            except ValueError:
                error(f"Invalid date: {today}")
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    filtered = list(tasks)

    # Tag filter
    if tag_filter is not None:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    # Overdue filter
    if overdue:
        if today is None:
            today = date.today().isoformat()
        today_dt = date.fromisoformat(today)
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today_dt
        ]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(task_line(task))


def do_done(args):
    """Handle the 'done' command."""
    tasks, next_id = load_data()
    history = load_history()

    if not args:
        error("done requires an ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state for undo
    prev_state = {"tasks": [t for t in tasks], "next_id": next_id}
    history.append(prev_state)
    save_history(history)

    task["done"] = True
    save_data(tasks, next_id)
    print(f"Done {task_id}")


def do_delete(args):
    """Handle the 'delete' command."""
    tasks, next_id = load_data()
    history = load_history()

    if not args:
        error("delete requires an ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state for undo
    prev_state = {"tasks": [t for t in tasks], "next_id": next_id}
    history.append(prev_state)
    save_history(history)

    tasks = [t for t in tasks if t["id"] != task_id]
    save_data(tasks, next_id)
    print(f"Deleted {task_id}")


def do_edit(args):
    """Handle the 'edit' command."""
    tasks, next_id = load_data()
    history = load_history()

    if not args:
        error("edit requires an ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = None
    for t in tasks:
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
            new_title = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    if new_title is None:
        error("edit --title requires a new title")

    # Save state for undo
    prev_state = {"tasks": [t for t in tasks], "next_id": next_id}
    history.append(prev_state)
    save_history(history)

    task["title"] = new_title
    save_data(tasks, next_id)
    print(f"Edited {task_id}")


def do_search(args):
    """Handle the 'search' command."""
    tasks, next_id = load_data()

    if not args:
        error("search requires text")

    query = " ".join(args).lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def do_export(args):
    """Handle the 'export' command."""
    tasks, next_id = load_data()

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

    if fmt is None:
        error("--format is required")

    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Invalid format: {fmt}")


def do_stats(args):
    """Handle the 'stats' command."""
    tasks, next_id = load_data()

    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)

    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(args):
    """Handle the 'undo' command."""
    history = load_history()

    if not history:
        error("Nothing to undo")

    prev_state = history.pop()
    save_history(history)
    save_data(prev_state["tasks"], prev_state["next_id"])
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "add": do_add,
        "list": do_list,
        "done": do_done,
        "delete": do_delete,
        "edit": do_edit,
        "search": do_search,
        "export": do_export,
        "stats": do_stats,
        "undo": do_undo,
    }

    if command not in commands:
        error(f"Unknown command: {command}")

    commands[command](args)


if __name__ == "__main__":
    main()
