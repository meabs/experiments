#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os

DATA_FILE = "tasks.json"


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string."""
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def load_tasks():
    """Load tasks from the data file, or return empty state if not found."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1, "history": []}


def save_tasks(data):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def format_task_line(task):
    """Format a task into the display line format."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix (F05)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix (F06)
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix (F07)
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def find_task(data, task_id):
    """Find a task by id. Returns (index, task) or (None, None)."""
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            return i, task
    return None, None


def add_task(data, title, priority="medium", tags=None, due=None):
    """Add a new task with the given title."""
    if tags is None:
        tags = []
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    # Save current state to history before mutating
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    data["tasks"].append(task)
    data["next_id"] += 1
    save_tasks(data)
    print(f"Added {task['id']}")


def cmd_add(args):
    """Handle the 'add' command."""
    if not args:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    # Parse options from args
    priority = "medium"
    tags = []
    due = None
    title_parts = []
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
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    add_task(data, title, priority, tags, due)


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_tasks()

    # Parse options
    sort_by = None
    filter_tag = None
    overdue = False
    today = None

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
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a value", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = data["tasks"]

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue (only open tasks due before today)
    if overdue:
        if today is None:
            from datetime import date
            today = date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

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
    """Handle the 'done' command."""
    if not args:
        print("Error: missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid task ID '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state to history
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    task["done"] = True
    save_tasks(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        print("Error: missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid task ID '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state to history
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    data["tasks"].pop(idx)
    save_tasks(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    if not args:
        print("Error: missing task ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid task ID '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    # Parse --title option
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            # Collect all remaining args as title
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        print("Error: missing --title", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state to history
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    task["title"] = new_title
    save_tasks(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        print("Error: missing search text", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    data = load_tasks()

    # Find tasks whose title contains the query (case-insensitive)
    results = [t for t in data["tasks"] if query in t["title"].lower()]
    # Sort by id
    results.sort(key=lambda t: t["id"])

    if not results:
        print("No matches")
        return

    for task in results:
        print(format_task_line(task))


def main():
    if len(sys.argv) < 2:
        print("Error: no command given", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "add":
        cmd_add(args)
    elif command == "list":
        cmd_list(args)
    elif command == "done":
        cmd_done(args)
    elif command == "delete":
        cmd_delete(args)
    elif command == "edit":
        cmd_edit(args)
    elif command == "search":
        cmd_search(args)
    else:
        print(f"Error: unknown command '{command}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
