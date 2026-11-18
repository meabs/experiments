#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    """Load tasks from the data file."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    """Save tasks and next_id to the data file."""
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    """Load undo history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    """Push current state onto the undo history."""
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_history(history)


def format_task_line(task):
    """Format a task for display."""
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due", None)
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args):
    """Add a new task."""
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if month < 1 or month > 12:
                    raise ValueError
                if day < 1 or day > 31:
                    raise ValueError
            except (ValueError, IndexError):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    push_history(tasks, next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    next_id += 1
    save_tasks(tasks, next_id)
    print(f"Added {task['id']}")


def cmd_list(args):
    """List tasks."""
    tasks, _ = load_tasks()
    sort_by = None
    tag_filter = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if today is None:
        import datetime
        today = datetime.date.today().isoformat()

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = None
    for task in tasks:
        if task["id"] == task_id:
            found = task
            break

    if found is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(tasks, next_id)
    found["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = None
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            found = i
            break

    if found is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(tasks, next_id)
    tasks.pop(found)
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = None
    for task in tasks:
        if task["id"] == task_id:
            found = task
            break

    if found is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            i += 1
            while i < len(args) and args[i] != "--title":
                title_parts.append(args[i])
                i += 1
        else:
            i += 1

    if not title_parts:
        print("Missing new title", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(title_parts)

    push_history(tasks, next_id)
    found["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title substring."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Print task statistics."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": lambda args: undo(),
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
