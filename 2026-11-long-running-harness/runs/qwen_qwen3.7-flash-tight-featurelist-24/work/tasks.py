#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_data():
    """Load tasks and next_id from data file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": {}, "next_id": 1}


def save_data(data):
    """Save tasks and next_id to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    """Load undo history from undo file."""
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo_history(history):
    """Save undo history to undo file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def validate_date(date_str):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return False
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        d = date(year, month, day)
        return True
    except (ValueError, IndexError):
        return False


def format_task_line(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'

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
    if task.get("due"):
        line += f' due:{task["due"]}'

    return line


def cmd_add(args, data, undo_history):
    """Handle 'add' command."""
    title_parts = []
    priority = None
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
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
            due = args[i + 1]
            if not validate_date(due):
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        error("add requires a TITLE")

    new_id = data["next_id"]
    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }

    # Record state for undo
    undo_history.append({
        "action": "add",
        "data": json.loads(json.dumps(data)),
        "next_id": data["next_id"],
    })

    data["tasks"][new_id] = task
    data["next_id"] = new_id + 1
    save_data(data)
    save_undo_history(undo_history)
    print(f"Added {new_id}")


def cmd_list(args, data, undo_history):
    """Handle 'list' command."""
    sort_by = None
    filter_tag = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if today:
        today = datetime.strptime(today, "%Y-%m-%d").date()
    else:
        today = date.today()

    tasks = list(data["tasks"].values())

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue: only open tasks with due date before today
    if overdue:
        tasks = [
            t for t in tasks
            if not t["done"]
            and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data, undo_history):
    """Handle 'done' command."""
    if not args or not args[0].isdigit():
        error("done requires an ID")

    task_id = int(args[0])
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    undo_history.append({
        "action": "done",
        "data": json.loads(json.dumps(data)),
        "next_id": data["next_id"],
    })

    data["tasks"][task_id]["done"] = True
    save_data(data)
    save_undo_history(undo_history)
    print(f"Done {task_id}")


def cmd_delete(args, data, undo_history):
    """Handle 'delete' command."""
    if not args or not args[0].isdigit():
        error("delete requires an ID")

    task_id = int(args[0])
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    undo_history.append({
        "action": "delete",
        "data": json.loads(json.dumps(data)),
        "next_id": data["next_id"],
    })

    del data["tasks"][task_id]
    save_data(data)
    save_undo_history(undo_history)
    print(f"Deleted {task_id}")


def cmd_edit(args, data, undo_history):
    """Handle 'edit' command."""
    if not args or not args[0].isdigit():
        error("edit requires an ID")

    task_id = int(args[0])
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

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
            break
        else:
            i += 1

    if not new_title:
        error("edit requires --title NEW TITLE")

    undo_history.append({
        "action": "edit",
        "data": json.loads(json.dumps(data)),
        "next_id": data["next_id"],
    })

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    save_undo_history(undo_history)
    print(f"Edited {task_id}")


def cmd_search(args, data, undo_history):
    """Handle 'search' command."""
    if not args:
        error("search requires TEXT")

    text = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if text in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data, undo_history):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt:
        error("export requires --format json|csv")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args, data, undo_history):
    """Handle 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data, undo_history):
    """Handle 'undo' command."""
    if not undo_history:
        error("Nothing to undo")

    last_action = undo_history.pop()
    data = last_action["data"]
    data["next_id"] = last_action["next_id"]
    save_data(data)
    save_undo_history(undo_history)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_data()
    undo_history = load_undo_history()

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

    if command not in commands:
        error(f"Unknown command: {command}")

    handler = commands[command]
    handler(args, data, undo_history)


if __name__ == "__main__":
    main()
