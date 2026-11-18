#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args, data):
    """Handle 'add' command."""
    title_parts = []
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
            due = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Record undo state before mutation
    data["undo_history"].append({
        "type": "add",
        "task_id": task["id"],
        "prev_next_id": data["next_id"],
    })

    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
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

    if overdue:
        if today_str is None:
            today = date.today().isoformat()
        else:
            today = today_str
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]

    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    if not tasks:
        print("No tasks")
        return

    if sort_priority:
        order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (order.get(t["priority"], 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Record undo state
    data["undo_history"].append({
        "type": "done",
        "task_id": task_id,
        "prev_done": task["done"],
    })

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Record undo state
    data["undo_history"].append({
        "type": "delete",
        "task_id": task_id,
        "prev_task": task,
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

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
            # Collect all remaining args as new title
            new_title = " ".join(args[i + 1:])
            break
        else:
            i += 1

    if new_title is None:
        error("Missing --title")

    # Record undo state
    data["undo_history"].append({
        "type": "edit",
        "task_id": task_id,
        "prev_title": task["title"],
    })

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    matches = []
    for task in data["tasks"]:
        if query in task["title"].lower():
            matches.append(task)

    if not matches:
        print("No matches")
        return

    # Already in id order since we iterate in order
    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format")

    if fmt not in ("json", "csv"):
        error(f"Invalid format: {fmt}")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["undo_history"]:
        error("Nothing to undo")

    entry = data["undo_history"].pop()

    if entry["type"] == "add":
        data["tasks"] = [t for t in data["tasks"] if t["id"] != entry["task_id"]]
        data["next_id"] = entry["prev_next_id"]
    elif entry["type"] == "done":
        task = next((t for t in data["tasks"] if t["id"] == entry["task_id"]), None)
        if task:
            task["done"] = entry["prev_done"]
    elif entry["type"] == "delete":
        data["tasks"].append(entry["prev_task"])
        data["tasks"].sort(key=lambda t: t["id"])
    elif entry["type"] == "edit":
        task = next((t for t in data["tasks"] if t["id"] == entry["task_id"]), None)
        if task:
            task["title"] = entry["prev_title"]

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

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
