#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from the data file, or return empty list if not found."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix (feature 5)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix (feature 6)
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix (feature 7)
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Add a new task."""
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            # Validate date
            try:
                date.fromisoformat(due)
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks, next_id = load_tasks()

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print(f"Added {task['id']}")


def cmd_list(args):
    """List all tasks."""
    tasks, _ = load_tasks()

    # Parse options
    filter_tag = None
    sort_by = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("Missing value for --today", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)

    if today is None:
        today = date.today().isoformat()

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue (only open tasks due before today)
    if overdue:
        today_date = date.fromisoformat(today)
        tasks = [
            t
            for t in tasks
            if not t["done"]
            and t.get("due")
            and date.fromisoformat(t["due"]) < today_date
        ]

    # Sort by priority
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(
            tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"])
        )

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks, next_id)
            print(f"Done {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Delete a task."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            save_tasks(tasks, next_id)
            print(f"Deleted {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    """Edit a task's title."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)

    task_id_str = args[0]
    try:
        task_id = int(task_id_str)
    except ValueError:
        print(f"No such task: {task_id_str}", file=sys.stderr)
        sys.exit(1)

    # Find --title flag
    title_idx = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            title_idx = i + 1
            break
        i += 1

    if title_idx is None or title_idx >= len(args):
        print("Missing --title argument", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(args[title_idx:])
    tasks, next_id = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            save_tasks(tasks, next_id)
            print(f"Edited {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Search tasks by title."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    tasks, _ = load_tasks()

    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing value for --format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if fmt != "json" and fmt != "csv":
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            priority_str = t.get("priority", "medium")
            print(f'{t["id"]},{t["title"]},{done_str},{priority_str},{tags_str},{due_str}')


def cmd_stats(args):
    """Print statistics about tasks."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    history_file = "tasks_history.json"

    if not os.path.exists(history_file):
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    with open(history_file, "r") as f:
        history = json.load(f)

    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    state = history[-1]
    # Restore previous state
    save_tasks(state["tasks"], state["next_id"])
    history.pop()
    with open(history_file, "w") as f:
        json.dump(history, f)
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

    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
