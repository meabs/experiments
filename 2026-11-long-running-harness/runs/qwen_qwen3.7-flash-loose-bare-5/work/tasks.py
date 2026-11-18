#!/usr/bin/env python3
"""A command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    """Load tasks and next_id from tasks.json. Return ([], 1) if file doesn't exist."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data["tasks"], data["next_id"]


def save_tasks(tasks, next_id):
    """Save tasks and next_id to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo():
    """Load undo history from undo.json. Return [] if file doesn't exist."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(history):
    """Save undo history to undo.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix: only non-medium
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix: in order given
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_args(argv):
    """Parse command-line arguments into command, positional args, and options dict."""
    if not argv:
        return None, [], {}

    command = argv[0]
    args = argv[1:]
    options = {}
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("Missing value for --priority")
            options["priority"] = args[i]
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing value for --tag")
            if "tags" not in options:
                options["tags"] = []
            options["tags"].append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("Missing value for --due")
            options["due"] = args[i]
        elif arg == "--title":
            i += 1
            if i >= len(args):
                error("Missing value for --title")
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            options["title"] = " ".join(title_parts)
            i -= 1
        elif arg == "--sort":
            i += 1
            if i >= len(args):
                error("Missing value for --sort")
            options["sort"] = args[i]
        elif arg == "--overdue":
            options["overdue"] = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                error("Missing value for --today")
            options["today"] = args[i]
        elif arg == "--format":
            i += 1
            if i >= len(args):
                error("Missing value for --format")
            options["format"] = args[i]
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            positional.append(arg)
        i += 1

    return command, positional, options


def do_add(tasks, next_id, args, options):
    """Handle the 'add' command."""
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = args[0]

    priority = options.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")

    tags = options.get("tags", [])

    due = options.get("due", None)
    if due is not None:
        try:
            date.fromisoformat(due)
        except (ValueError, TypeError):
            error(f"Invalid date: {due}")

    new_task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(new_task)
    next_id += 1

    save_tasks(tasks, next_id)
    print(f"Added {new_task['id']}")


def do_list(tasks, next_id, args, options):
    """Handle the 'list' command."""
    filtered = list(tasks)

    # Filter by tag(s)
    tag_filter = options.get("tags")
    if tag_filter:
        filtered = [t for t in filtered if any(tag in t.get("tags", []) for tag in tag_filter)]

    # Filter overdue
    if options.get("overdue"):
        today_str = options.get("today", date.today().isoformat())
        try:
            today = date.fromisoformat(today_str)
        except (ValueError, TypeError):
            error(f"Invalid date: {today_str}")
        filtered = [t for t in filtered if not t["done"] and t.get("due") and t["due"] < today_str]

    # Sort
    sort_mode = options.get("sort")
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    elif sort_mode:
        error(f"Unknown sort mode: {sort_mode}")

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(task_line(task))


def do_done(tasks, next_id, args, options):
    """Handle the 'done' command."""
    if not args:
        error("Usage: done ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    task["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def do_delete(tasks, next_id, args, options):
    """Handle the 'delete' command."""
    if not args:
        error("Usage: delete ID")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    tasks.remove(task)
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def do_edit(tasks, next_id, args, options):
    """Handle the 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    if "title" not in options:
        error("Usage: edit ID --title NEW TITLE")

    task["title"] = options["title"]
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def do_search(tasks, next_id, args, options):
    """Handle the 'search' command."""
    if not args:
        error("Usage: search TEXT")

    query = args[0].lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def do_export(tasks, next_id, args, options):
    """Handle the 'export' command."""
    fmt = options.get("format")
    if fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")

    sorted_tasks = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in sorted_tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in sorted_tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")


def do_stats(tasks, next_id, args, options):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def do_undo(tasks, next_id, args, options):
    """Handle the 'undo' command."""
    history = load_undo()

    if not history:
        error("Nothing to undo")

    prev_state = history.pop()
    save_undo(history)
    save_tasks(prev_state["tasks"], prev_state["next_id"])
    print("Undone")


MUTATING_COMMANDS = {"add", "done", "delete", "edit"}


COMMANDS = {
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


def main():
    command, positional, options = parse_args(sys.argv[1:])

    if command is None:
        error("Usage: python3 tasks.py <command> [args]")

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    tasks, next_id = load_tasks()

    # For mutating commands, push current state to undo history before modifying
    if command in MUTATING_COMMANDS:
        history = load_undo()
        history.append({"tasks": tasks, "next_id": next_id})
        save_undo(history)

    COMMANDS[command](tasks, next_id, positional, options)


if __name__ == "__main__":
    main()
