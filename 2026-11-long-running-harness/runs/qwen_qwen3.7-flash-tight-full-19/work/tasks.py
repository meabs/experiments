#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def print_error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Add a new task."""
    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print_error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print_error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print_error("--tag requires an argument")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print_error("Invalid date: ")
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print_error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print_error("add requires a title")

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = task_id + 1
    # Save undo state before mutation
    data["history"].append({"state": _snapshot_before(data)})
    save_data(data)
    print(f"Added {task_id}")


def _snapshot_before(data):
    """Create a snapshot of the data state."""
    return {
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }


def cmd_list(args):
    """List tasks."""
    data = load_data()
    tasks = list(data["tasks"].values())
    if not tasks:
        print("No tasks")
        return

    # Parse options
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    # Overdue: only open tasks with due date before today
    if overdue:
        if today_str:
            try:
                today_iso = today_str
                datetime.strptime(today_iso, "%Y-%m-%d")
            except ValueError:
                print_error(f"Invalid date: {today_str}")
        else:
            today_iso = date.today().strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_iso]

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        print_error("done requires an ID")
    try:
        task_id = int(args[0])
    except ValueError:
        print_error(f"No such task: {args[0]}")

    data = load_data()
    if task_id not in data["tasks"]:
        print_error(f"No such task: {task_id}")

    data["tasks"][task_id]["done"] = True
    data["history"].append({"state": _snapshot_before(data)})
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    if not args:
        print_error("delete requires an ID")
    try:
        task_id = int(args[0])
    except ValueError:
        print_error(f"No such task: {args[0]}")

    data = load_data()
    if task_id not in data["tasks"]:
        print_error(f"No such task: {task_id}")

    del data["tasks"][task_id]
    data["history"].append({"state": _snapshot_before(data)})
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    if not args:
        print_error("edit requires an ID")
    try:
        task_id = int(args[0])
    except ValueError:
        print_error(f"No such task: {args[0]}")

    data = load_data()
    if task_id not in data["tasks"]:
        print_error(f"No such task: {task_id}")

    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
            break
        else:
            i += 1

    if not new_title_parts:
        print_error("edit --title requires a new title")

    new_title = " ".join(new_title_parts)
    data["tasks"][task_id]["title"] = new_title
    data["history"].append({"state": _snapshot_before(data)})
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title substring."""
    if not args:
        print_error("search requires TEXT")
    query = " ".join(args).lower()
    data = load_data()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    if not args:
        print_error("export requires --format json|csv")

    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        print_error("export requires --format json|csv")

    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for task in tasks:
            result.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "due": task["due"],
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task["tags"])
            due_str = task["due"] if task["due"] else ""
            print(f"{task['id']},{task['title']},{done_str},{task['priority']},{tags_str},{due_str}")


def cmd_stats(args):
    """Print task statistics."""
    data = load_data()
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()
    if not data["history"]:
        print_error("Nothing to undo")
    prev_state = data["history"].pop()["state"]
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print_error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

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
        print_error(f"Unknown command: {command}")

    commands[command](args)


if __name__ == "__main__":
    main()
