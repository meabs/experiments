#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    """Save tasks to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task, full=True):
    """Format a task as a display line.
    
    Args:
        task: dict with keys id, title, done, priority, tags, due
        full: if True, include all suffixes; if False, just id/title/done
    
    Returns:
        Formatted string like "<id> [ ] <title>" or "<id> [x] <title> (high) #work due:2026-01-01"
    """
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]
    
    if full:
        # Priority suffix
        if task.get("priority") == "high":
            parts.append("(high)")
        elif task.get("priority") == "low":
            parts.append("(low)")
        # medium has no suffix
        
        # Tags suffix
        if task.get("tags"):
            for tag in task["tags"]:
                parts.append(f"#{tag}")
        
        # Due date suffix
        if task.get("due"):
            parts.append(f"due:{task['due']}")
    
    return " ".join(parts)


def add_task(args, data):
    """Add a new task."""
    if not args:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    # Parse options
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    
    title = " ".join(title_parts)
    if not title:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    task_id = data["next_id"]
    data["next_id"] += 1

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)

    # Save undo history for add
    data["history"].append({
        "type": "add",
        "task": task,
    })

    save_tasks(data)
    print(f"Added {task_id}")


def list_tasks(args, data):
    """List tasks."""
    import datetime
    
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    
    tasks = data["tasks"]
    
    # Apply filters
    filtered = []
    for t in tasks:
        if tag_filter and tag_filter not in t.get("tags", []):
            continue
        if overdue:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = datetime.date.fromisoformat(t["due"])
                    today = datetime.date.today() if today_str is None else datetime.date.fromisoformat(today_str)
                    if due_date >= today:
                        continue
                except ValueError:
                    pass
            else:
                continue
        filtered.append(t)
    
    if not filtered:
        print("No tasks")
        return
    
    # Apply sorting
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    # Default: sort by id
    
    for t in filtered:
        print(task_line(t))


def done_task(args, data):
    """Mark a task as done."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    found = False
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            found = True
            break
    
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    
    # Save undo history for done
    data["history"].append({
        "type": "done",
        "task_id": task_id,
    })
    
    save_tasks(data)
    print(f"Done {task_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_tasks()

    if command == "add":
        add_task(args, data)
    elif command == "list":
        list_tasks(args, data)
    elif command == "done":
        done_task(args, data)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
