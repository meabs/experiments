#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from file or return initial state."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    """Save tasks data to file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    done_marker = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {done_marker} {task['title']}"]
    # priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def make_snapshot(data):
    """Create a deep-copy snapshot of mutable state for undo."""
    return {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }


def add_task(args, data):
    """Handle 'add' command."""
    title_parts = []
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
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)
    snapshot = make_snapshot(data)
    data["history"].append(snapshot)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] += 1
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task['id']}")


def list_tasks(args, data):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg.startswith("--today"):
            if arg == "--today":
                if i + 1 >= len(args):
                    error("--today requires a value")
                today_str = args[i + 1]
                i += 2
            else:
                # --today=value
                today_str = arg.split("=", 1)[1]
                i += 1
        else:
            i += 1

    tasks = list(data["tasks"])

    # Filter by tag if specified
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue if specified
    if overdue:
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        today_str_val = today.strftime("%Y-%m-%d")
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_str_val
        ]

    # Sort by priority if requested
    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def done_task(args, data):
    """Handle 'done' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = find_task(data, tid)
    if task is None:
        error(f"No such task: {tid}")

    snapshot = make_snapshot(data)
    data["history"].append(snapshot)

    task["done"] = True
    save_data(data)
    print(f"Done {tid}")


def delete_task(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = find_task(data, tid)
    if task is None:
        error(f"No such task: {tid}")

    snapshot = make_snapshot(data)
    data["history"].append(snapshot)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print(f"Deleted {tid}")


def edit_task(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = find_task(data, tid)
    if task is None:
        error(f"No such task: {tid}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            # Collect all remaining arguments after --title as the new title
            new_title = " ".join(args[i + 1:])
            break
        else:
            i += 1

    if new_title is None:
        error("Missing --title")

    snapshot = make_snapshot(data)
    data["history"].append(snapshot)

    task["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def search_tasks(args, data):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"], key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def export_tasks(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

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
                "due": t.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")


def stats_tasks(args, data):
    """Handle 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def undo_command(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")

    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


def find_task(data, tid):
    """Find a task by id."""
    for t in data["tasks"]:
        if t["id"] == tid:
            return t
    return None


def main():
    if len(sys.argv) < 2:
        error("Usage: tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]
    data = load_data()

    commands = {
        "add": add_task,
        "list": list_tasks,
        "done": done_task,
        "delete": delete_task,
        "edit": edit_task,
        "search": search_tasks,
        "export": export_tasks,
        "stats": stats_tasks,
        "undo": undo_command,
    }

    handler = commands.get(command)
    if handler is None:
        error(f"Unknown command: {command}")

    try:
        handler(args, data)
    except SystemExit:
        raise
    except Exception as e:
        error(str(e))


if __name__ == "__main__":
    main()
