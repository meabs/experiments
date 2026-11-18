#!/usr/bin/env python3
"""A command-line task manager using only Python 3 standard library."""

import json
import os
import sys
import copy
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task_line(task):
    """Format a task for display."""
    done_marker = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_marker} {task['title']}"
    # Priority suffix (medium has no suffix)
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # Tags suffix
    for tag in task["tags"]:
        line += f" #{tag}"
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Handle 'add' command."""
    data = load_data()
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
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
            due_str = args[i + 1]
            try:
                date.fromisoformat(due_str)
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        elif args[i].startswith("--"):
            error(f"Unknown option: {args[i]}")
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        error("Usage: add TITLE [options]")

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

    # Save undo state before mutating
    data["undo_stack"].append(copy.deepcopy(data))
    save_data(data)

    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
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

    tasks = data["tasks"]

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    # Overdue filter: only open tasks due before today
    if overdue:
        if today_str:
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                error(f"Invalid date: {today_str}")
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Handle 'done' command."""
    data = load_data()
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    task["done"] = True
    data["undo_stack"].append(copy.deepcopy(data))
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    data = load_data()
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    data["tasks"].remove(task)
    data["undo_stack"].append(copy.deepcopy(data))
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    data = load_data()
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")

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
                error("Missing value for --title")
            parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            continue
        i += 1

    if new_title is None:
        error("Missing --title")

    task["title"] = new_title
    data["undo_stack"].append(copy.deepcopy(data))
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    data = load_data()
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    results = []
    for task in data["tasks"]:
        if query in task["title"].lower():
            results.append(task)

    if not results:
        print("No matches")
        return

    for task in results:
        print(format_task_line(task))


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
        error("Usage: export --format json|csv")

    if fmt == "json":
        export_tasks = []
        for t in data["tasks"]:
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
        for t in data["tasks"]:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()
    if not data["undo_stack"]:
        error("Nothing to undo")
    data = data["undo_stack"].pop()
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
        error("Usage: tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
