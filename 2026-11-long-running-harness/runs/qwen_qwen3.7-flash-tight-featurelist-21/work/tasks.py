#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and next_id from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and next_id to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def parse_add_flags(args):
    """Parse flags from add command args, return (title_parts, priority, tags, due)."""
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority:", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    return title_parts, priority, tags, due


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix: only show (high) or (low)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
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
    title_parts, priority, tags, due = parse_add_flags(args)
    
    if not title_parts:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)
    
    title = " ".join(title_parts)
    
    if priority is None:
        priority = "medium"
    
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


def cmd_list(args, data):
    """List all tasks."""
    tasks = list(data["tasks"])
    
    # Check for --tag filter
    tag_filter = None
    sort_priority = False
    overdue_filter = False
    today = None
    
    i = 0
    while i < len(args):
        if args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--sort" and i + 1 < len(args):
            sort_option = args[i + 1]
            if sort_option == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--overdue":
            overdue_filter = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1
    
    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    
    # Filter overdue
    if overdue_filter:
        import datetime
        if today is None:
            today = datetime.date.today().isoformat()
        try:
            today_date = datetime.date.fromisoformat(today)
        except ValueError:
            print(f"Invalid date: {today}", file=sys.stderr)
            sys.exit(1)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    
    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    
    if not tasks:
        print("No tasks")
        return
    
    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    try:
        task_id = int(args[0])
    except (IndexError, ValueError):
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            save_data(data)
            print(f"Done {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args, data):
    """Delete a task."""
    try:
        task_id = int(args[0])
    except (IndexError, ValueError):
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"].pop(i)
            save_data(data)
            print(f"Deleted {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]
    data = load_data()

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
        "delete": cmd_delete,
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args, data)


if __name__ == "__main__":
    main()
