#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
import copy
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        if "tasks" not in data:
            data["tasks"] = {}
        if "next_id" not in data:
            data["next_id"] = 1
        if "history" not in data:
            data["history"] = []
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "history": []}


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task(task):
    """Format a task for display."""
    check = "x" if task["done"] else " "
    line = f"{task['id']} [{check}] {task['title']}"
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
    """Handle 'add' command."""
    if not args:
        error("Missing title")

    data = load_data()
    title_parts = []
    i = 0
    priority = "medium"
    tags = []
    due = None

    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("Missing priority value")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing tag value")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("Missing due date value")
            due = args[i]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)
    task_id = data["next_id"]

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Save state for undo
    data["history"].append({
        "action": "add",
        "state": copy.deepcopy(data),
    })

    data["tasks"][str(task_id)] = task
    data["next_id"] = task_id + 1
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    sort_priority = False
    filter_tag = None
    filter_overdue = False
    filter_today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                error("Missing sort value")
            if args[i] == "priority":
                sort_priority = True
            else:
                error(f"Invalid sort: {args[i]}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing tag value")
            filter_tag = args[i]
        elif arg == "--overdue":
            filter_overdue = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                error("Missing today value")
            filter_today = args[i]
        else:
            i += 1

    if filter_today is None:
        filter_today = date.today().isoformat()

    # Filter tasks
    filtered = []
    for task in tasks:
        # Apply tag filter
        if filter_tag and filter_tag not in task.get("tags", []):
            continue

        # Apply overdue filter
        if filter_overdue:
            if task["done"]:
                continue
            if not task.get("due"):
                continue
            if task["due"] >= filter_today:
                continue

        filtered.append(task)

    if not filtered:
        print("No tasks")
        return

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    for task in filtered:
        print(format_task(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        error("Missing task ID")

    data = load_data()
    task_id = int(args[0])

    if str(task_id) not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["history"].append({
        "action": "done",
        "state": copy.deepcopy(data),
    })

    data["tasks"][str(task_id)]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Missing task ID")

    data = load_data()
    task_id = int(args[0])

    if str(task_id) not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["history"].append({
        "action": "delete",
        "state": copy.deepcopy(data),
    })

    del data["tasks"][str(task_id)]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Missing task ID")

    data = load_data()
    task_id = int(args[0])

    if str(task_id) not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Parse --title argument
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                error("Missing title value")
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            break
        i += 1

    if new_title is None:
        error("Missing --title option")

    # Save state for undo
    data["history"].append({
        "action": "edit",
        "state": copy.deepcopy(data),
    })

    data["tasks"][str(task_id)]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    data = load_data()
    query = args[0].lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()
    fmt = None

    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("Missing format value")
            fmt = args[i]
        i += 1

    if fmt is None:
        error("Missing --format option")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(export_data))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{done_str},{task.get('priority', 'medium')},{tags_str},{due_str}")

    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(list(tasks))
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()

    if not data["history"]:
        error("Nothing to undo")

    previous_state = data["history"].pop()["state"]
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
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
    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
