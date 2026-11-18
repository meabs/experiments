#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Persist tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def format_task_line(task):
    """Format a single task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def snapshot(data):
    """Save a snapshot of current state for undo. Stores only tasks+next_id."""
    snap = {"tasks": list(data["tasks"]), "next_id": data["next_id"]}
    data["history"].append(snap)


def cmd_add(args, data):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
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
                print("Missing due date", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    task_id = data["next_id"]
    new_task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    snapshot(data)
    data["tasks"].append(new_task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_by = None
    filter_tag = None
    overdue = False
    today_arg = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = list(data["tasks"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    # Overdue filter: only open tasks with due date before today
    if overdue:
        if today_arg:
            cutoff = today_arg
        else:
            cutoff = date.today().strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < cutoff]

    # Sort by priority
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task ID", file=sys.stderr)
        sys.exit(1)

    found = None
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    snapshot(data)
    found["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task ID", file=sys.stderr)
        sys.exit(1)

    found = None
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task ID", file=sys.stderr)
        sys.exit(1)

    found = None
    for task in data["tasks"]:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Parse --title flag
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            new_title_parts.append(args[i + 1])
            i += 2
        else:
            i += 1

    if not new_title_parts:
        print("Missing new title", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(new_title_parts)

    snapshot(data)
    found["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    matches = []
    for task in data["tasks"]:
        if query in task["title"].lower():
            matches.append(task)

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format argument", file=sys.stderr)
        sys.exit(1)

    if fmt == "json":
        export_data = []
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task["tags"],
                "due": task["due"],
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task["tags"])
            due_str = task["due"] if task["due"] else ""
            print(f"{task['id']},{task['title']},{done_str},{task['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Handle 'stats' command."""
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
