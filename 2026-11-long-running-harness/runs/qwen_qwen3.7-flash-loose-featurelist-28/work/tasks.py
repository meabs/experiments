#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from the data file, or return empty list."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", [])
    return []


def get_next_id(tasks):
    """Get the next available task id (never reused)."""
    # Read stored next_id from file to ensure IDs are never reused
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("_next_id", 1)
    return 1


def save_all(data):
    """Save full data dict to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_tasks(tasks):
    """Save tasks to the data file, preserving metadata like _next_id."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data["tasks"] = tasks
    save_all(data)


def format_task_line(task):
    """Format a task for display: <id> [ ] <title> or <id> [x] <title>.
    Suffixes appended in order: priority, tags, due date."""
    status = "x" if task.get("done", False) else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args):
    """Add a new task."""
    if not args:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    # Parse flags
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Error: --priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Error: --due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority is not None and priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate date if provided
    if due is not None:
        import datetime
        try:
            datetime.datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    title = " ".join(title_parts)
    tasks = load_tasks()
    task_id = get_next_id(tasks)
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    # Update _next_id atomically
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data["tasks"] = tasks
    data["_next_id"] = task_id + 1
    save_all(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """List all tasks in id order, with optional filtering and sorting."""
    tasks = load_tasks()
    if not tasks:
        print("No tasks")
        return

    # Parse flags
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue (open tasks due before today)
    if overdue:
        import datetime
        if today_str:
            today = datetime.date.fromisoformat(today_str)
        else:
            today = datetime.date.today()
        tasks = [
            t for t in tasks
            if not t.get("done", False)
            and t.get("due")
            and datetime.date.fromisoformat(t["due"]) < today
        ]

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        print("Error: missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid task ID", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task by ID."""
    if not args:
        print("Error: missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid task ID", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(new_tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    if not args:
        print("Error: missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid task ID", file=sys.stderr)
        sys.exit(1)

    # Parse --title flag - collect all remaining args as the new title
    new_title = None
    i = 1  # Start after task_id
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            # Collect all remaining arguments as the new title
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        print("Error: missing --title", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title substring (case-insensitive)."""
    if not args:
        print("Error: missing search text", file=sys.stderr)
        sys.exit(1)

    search_text = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
        "delete": cmd_delete,
        "edit": cmd_edit,
        "search": cmd_search,
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args)


if __name__ == "__main__":
    main()
