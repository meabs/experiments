#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_data():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_undo():
    """Load undo history."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(history):
    """Save undo history."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    """Format a task for display in list/search output."""
    line = f"{task['id']} [{'x' if task['done'] else ' '}] {task['title']}"
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
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    """Add a new task."""
    title = None
    priority = "medium"
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
            due = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None or title.strip() == "":
        error("Missing task title")

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

    # Record undo state
    undo = load_undo()
    undo.append({"action": "add", "data": data})
    save_undo(undo)

    print(f"Added {task['id']}")


def cmd_list(args, data):
    """List tasks."""
    sort_mode = None
    filter_tag = None

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
            today = None
            i += 1
            # Check for --today
            if i < len(args) and args[i] == "--today":
                if i + 1 >= len(args):
                    error("--today requires a date value")
                today = args[i + 1]
                try:
                    datetime.strptime(today, "%Y-%m-%d")
                except ValueError:
                    error(f"Invalid date: {today}")
                i += 2
            else:
                today = date.today().strftime("%Y-%m-%d")
            # Filter overdue tasks
            tasks = [t for t in data["tasks"] if not t["done"] and t.get("due") and t["due"] < today]
            tasks.sort(key=lambda t: t["id"])
            if not tasks:
                pass  # no output for empty
            else:
                for t in tasks:
                    print(format_task_line(t))
            return
        else:
            i += 1

    tasks = data["tasks"]

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(format_task_line(t))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    task["done"] = True
    save_data(data)

    # Record undo state
    undo = load_undo()
    undo.append({"action": "done", "data": data})
    save_undo(undo)

    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)

    # Record undo state
    undo = load_undo()
    undo.append({"action": "delete", "data": data})
    save_undo(undo)

    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

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
                error("--title requires a value")
            # Collect remaining args as title
            new_title = args[i + 1]
            j = i + 2
            while j < len(args) and not args[j].startswith("--"):
                new_title += " " + args[j]
                j += 1
            break
        else:
            i += 1

    if new_title is None or new_title.strip() == "":
        error("Missing new title")

    task["title"] = new_title
    save_data(data)

    # Record undo state
    undo = load_undo()
    undo.append({"action": "edit", "data": data})
    save_undo(undo)

    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()

    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task_line(t))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
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
                "due": t.get("due", None),
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Print stats."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    undo = load_undo()
    if not undo:
        error("Nothing to undo")

    entry = undo.pop()
    save_undo(undo)

    data = entry["data"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: tasks.py <command> [args]")

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
