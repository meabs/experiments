#!/usr/bin/env python3
"""A command-line task manager using only Python 3 standard library."""

import json
import os
import sys
from datetime import datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
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


def cmd_add(args, data):
    """Handle 'add' command."""
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
            due_val = args[i + 1]
            try:
                datetime.strptime(due_val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_val}")
            due = due_val
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)
    new_id = data["next_id"]
    data["tasks"][new_id] = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["next_id"] = new_id + 1

    # Record for undo
    data["undo_history"].append({
        "action": "add",
        "task_id": new_id,
    })

    save_data(data)
    print(f"Added {new_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_mode = None
    filter_tag = None
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
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date")
            today = args[i + 1]
            try:
                datetime.strptime(today, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today}")
            i += 2
        else:
            i += 1

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue:
        if today is None:
            today = datetime.now().strftime("%Y-%m-%d")
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        filtered = []
        for t in tasks:
            if not t["done"] and t.get("due"):
                due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                if due_date < today_date:
                    filtered.append(t)
        tasks = filtered

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    data["tasks"][task_id]["done"] = True

    # Record for undo
    data["undo_history"].append({
        "action": "done",
        "task_id": task_id,
        "prev_done": False,
    })

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    deleted_task = data["tasks"].pop(task_id)

    # Record for undo
    data["undo_history"].append({
        "action": "delete",
        "task_id": task_id,
        "task": deleted_task,
    })

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1

    if new_title is None:
        error("--title is required")

    prev_title = data["tasks"][task_id]["title"]
    data["tasks"][task_id]["title"] = new_title

    # Record for undo
    data["undo_history"].append({
        "action": "edit",
        "task_id": task_id,
        "prev_title": prev_title,
    })

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                error(f"Invalid format: {fmt}")
            i += 2
        else:
            i += 1

    if fmt is None:
        error("--format is required")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
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
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["undo_history"]:
        error("Nothing to undo")

    entry = data["undo_history"].pop()

    if entry["action"] == "add":
        task_id = entry["task_id"]
        del data["tasks"][task_id]
        data["next_id"] = task_id
    elif entry["action"] == "done":
        task_id = entry["task_id"]
        data["tasks"][task_id]["done"] = entry["prev_done"]
    elif entry["action"] == "delete":
        task_id = entry["task_id"]
        data["tasks"][task_id] = entry["task"]
    elif entry["action"] == "edit":
        task_id = entry["task_id"]
        data["tasks"][task_id]["title"] = entry["prev_title"]

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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
