#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load data from tasks.json, creating if necessary."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    """Save data to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a line for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix (high or low only; medium has no suffix)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f' due:{task["due"]}'
    return line


def find_task(data, task_id):
    """Find a task by id. Returns None if not found."""
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_data()

    title_parts = []
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            i += 1
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            i += 1
            tags.append(args[i])
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            i += 1
            due = args[i]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(title_parts)

    task_id = data["next_id"]
    data["next_id"] += 1

    # Save snapshot for undo BEFORE modifying tasks
    data["history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

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


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_data()

    sort_priority = False
    filter_tag = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            i += 1
            if args[i] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i]}")
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            i += 1
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing --today value")
            i += 1
            today = args[i]
            try:
                datetime.strptime(today, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today}")
        else:
            error(f"Unknown option: {arg}")
        i += 1

    tasks = list(data["tasks"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue:
        if today is None:
            today = datetime.now().strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort
    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (prio_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    data = load_data()

    if not args:
        error("Usage: done ID")

    task_id = int(args[0])
    task = find_task(data, task_id)
    if task is None:
        error(f"No such task: {task_id}")

    # Save snapshot for undo BEFORE modifying
    data["history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    data = load_data()

    if not args:
        error("Usage: delete ID")

    task_id = int(args[0])
    task = find_task(data, task_id)
    if task is None:
        error(f"No such task: {task_id}")

    # Save snapshot for undo BEFORE modifying
    data["history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    data = load_data()

    new_title = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            i += 1
            parts = []
            # Collect remaining args as title until we hit an unknown flag
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            error(f"Unexpected argument: {arg}")
        i += 1

    if not args:
        error("Usage: edit ID --title NEW TITLE")

    task_id = int(args[0])
    task = find_task(data, task_id)
    if task is None:
        error(f"No such task: {task_id}")

    if new_title is None:
        error("Usage: edit ID --title NEW TITLE")

    # Save snapshot for undo BEFORE modifying
    data["history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    data = load_data()

    if not args:
        error("Usage: search TEXT")

    query = " ".join(args).lower()

    matches = []
    for task in sorted(data["tasks"], key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    data = load_data()

    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            i += 1
            fmt = args[i]
            if fmt not in ("json", "csv"):
                error(f"Unknown format: {fmt}")
        else:
            error(f"Unknown option: {arg}")
        i += 1

    if fmt is None:
        error("Usage: export --format json|csv")

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
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", "") or "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()

    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)

    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    data = load_data()

    if not data["history"]:
        error("Nothing to undo")

    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

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
        "undo": cmd_undo,
    }

    handler = commands.get(command)
    if handler is None:
        error(f"Unknown command: {command}")

    handler(args)


if __name__ == "__main__":
    main()
