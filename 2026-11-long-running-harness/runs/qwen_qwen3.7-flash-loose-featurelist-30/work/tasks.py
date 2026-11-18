#!/usr/bin/env python3
"""Task manager - command-line tool using Python 3 standard library."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and history from data file, or return empty defaults."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    # Ensure all keys exist for forward compatibility
    data.setdefault("tasks", [])
    data.setdefault("next_id", 1)
    data.setdefault("history", [])
    return data


def save_data(data):
    """Save tasks and history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def push_history(data):
    """Push current state onto undo history before a mutating operation."""
    data["history"].append({
        "tasks": data["tasks"],
        "next_id": data["next_id"]
    })


def pop_history(data):
    """Pop previous state from undo history and restore it."""
    if not data["history"]:
        return None
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    return True


def find_task(data, task_id):
    """Find a task by id, return index or -1."""
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            return i
    return -1


def format_task(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]
    # Priority suffix (feature 5)
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium has no suffix
    # Tags suffix (feature 6)
    tags = task.get("tags", [])
    if tags:
        parts.extend([f"#{t}" for t in tags])
    # Due date suffix (feature 7)
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


# --- Commands ---

def cmd_add(data, args):
    """Handle 'add' command."""
    # Parse optional --priority flag
    priority = "medium"
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            remaining.append(args[i])
            i += 1

    if not remaining:
        print("Usage: add TITLE [--priority high|medium|low]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(remaining)

    push_history(data)

    task_id = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": [],
        "due": None
    }
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(data, args):
    """Handle 'list' command."""
    # Parse optional flags
    sort_priority = False
    tag_filter = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_priority = args[i + 1] == "priority"
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
                print("--today requires a date YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = data["tasks"]

    # Filter by tag
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue
    if overdue:
        from datetime import datetime, date
        if today is None:
            today_str = date.today().isoformat()
        else:
            today_str = today
        try:
            today_date = date.fromisoformat(today_str)
        except ValueError:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task(task))


def cmd_done(data, args):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    idx = find_task(data, task_id)
    if idx == -1:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(data)
    data["tasks"][idx]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(data, args):
    """Handle 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    idx = find_task(data, task_id)
    if idx == -1:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(data)
    data["tasks"].pop(idx)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(data, args):
    """Handle 'edit' command."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    idx = find_task(data, task_id)
    if idx == -1:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Parse --title flag
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
        else:
            i += 1

    if new_title is None:
        print("--title is required", file=sys.stderr)
        sys.exit(1)

    push_history(data)
    data["tasks"][idx]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(data, args):
    """Handle 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(data, args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due")
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(data, args):
    """Handle 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(data, args):
    """Handle 'undo' command."""
    if not pop_history(data):
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](data, args)


if __name__ == "__main__":
    main()
