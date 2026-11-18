#!/usr/bin/env python3
"""A command-line task manager."""

import json
import sys
import os
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def push_undo(data):
    """Push a snapshot of current state onto the undo stack."""
    data["undo_stack"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    parts = [f'{task["id"]} [{status}] {task["title"]}']
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # Tags suffix
    if task.get("tags"):
        parts.append(" ".join(f"#{t}" for t in task["tags"]))
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args):
    """Handle 'add' command."""
    title = None
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
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            if title is None:
                title = arg
            else:
                title = title + " " + arg
            i += 1

    if title is None:
        error("add requires a title")

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


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = list(data["tasks"])

    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_by = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    # Apply tag filter
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Apply overdue filter (only open tasks)
    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
        else:
            today = date.today()
        filtered = []
        for t in tasks:
            if not t["done"] and t.get("due"):
                due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                if due_date < today:
                    filtered.append(t)
        tasks = filtered

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        error("done requires an ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    found = False
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    # Push undo BEFORE modifying the task
    push_undo(data)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            break

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("delete requires an ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    found = False
    delete_idx = None
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            found = True
            delete_idx = i
            break

    if not found:
        error(f"No such task: {task_id}")

    # Push undo BEFORE deleting the task
    push_undo(data)
    data["tasks"].pop(delete_idx)

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("edit requires an ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    new_title = None
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            # Capture all remaining arguments as the new title
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        error("edit requires --title")

    data = load_data()
    found = False
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    # Push undo BEFORE modifying the task
    push_undo(data)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["title"] = new_title
            break

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        error("search requires TEXT")
    text = " ".join(args).lower()

    data = load_data()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("export requires --format")

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
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()
    if not data["undo_stack"]:
        error("Nothing to undo")
    prev = data["undo_stack"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
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
