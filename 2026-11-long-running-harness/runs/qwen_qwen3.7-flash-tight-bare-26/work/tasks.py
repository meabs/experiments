#!/usr/bin/env python3
"""Command-line task manager."""

import sys
import os
import json
import copy
import csv
import io
from datetime import date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    # Convert string keys to int for tasks dict
    data["tasks"] = {int(k): v for k, v in data["tasks"].items()}
    return data


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def make_task_line(task):
    """Build the display line for a task."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    # Tags suffix
    if task["tags"]:
        parts.extend(task["tags"])
    # Due date suffix
    if task["due"]:
        parts.append("due:" + task["due"])
    return " ".join(parts)


def cmd_add(args, data):
    """Add a new task."""
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
            if not is_valid_date(due):
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

    # Save state BEFORE mutation for undo support
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))

    data["tasks"][data["next_id"]] = task
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    """List tasks."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tag_filter = args[i + 1]
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
            error(f"Unknown argument: {args[i]}")

    today = today_str if today_str else date.today().isoformat()

    tasks = list(data["tasks"].values())

    # Filter by tag
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    # Filter overdue
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t["due"] and t["due"] < today:
                filtered.append(t)
        tasks = filtered

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(make_task_line(t))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")

    if tid not in data["tasks"]:
        error(f"No such task: {tid}")

    # Save state BEFORE mutation
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))

    data["tasks"][tid]["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")

    if tid not in data["tasks"]:
        error(f"No such task: {tid}")

    # Save state BEFORE mutation
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))

    del data["tasks"][tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")

    if tid not in data["tasks"]:
        error(f"No such task: {tid}")

    # Parse --title
    title_index = None
    for i, a in enumerate(args):
        if a == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            title_index = i + 1
            break

    if title_index is None:
        error("Missing --title")

    new_title = " ".join(args[title_index:])

    # Save state BEFORE mutation
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))

    data["tasks"][tid]["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Search tasks by title."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(make_task_line(t))


def cmd_export(args, data):
    """Export tasks."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown argument: {args[i]}")

    if not fmt:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_list = []
        for t in tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_list, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args, data):
    """Show task statistics."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args, data):
    """Undo the most recent mutation."""
    if not data["history"]:
        error("Nothing to undo")

    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


def is_valid_date(s):
    """Check if string is a valid YYYY-MM-DD date."""
    try:
        parts = s.split("-")
        if len(parts) != 3:
            return False
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        d = date(year, month, day)
        return True
    except (ValueError, IndexError):
        return False


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_data()

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

    commands[command](args, data)


if __name__ == "__main__":
    main()
