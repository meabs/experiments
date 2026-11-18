#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
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


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Add a new task."""
    data = load_data()

    # Parse arguments
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            i += 1
            if i >= len(args):
                error("Missing priority value")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                error("Missing tag value")
            tags.append(args[i])
        elif args[i] == "--due":
            i += 1
            if i >= len(args):
                error("Missing due date value")
            due = args[i]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
        else:
            title_parts.append(args[i])
        i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    # Save state for undo
    data["undo_history"].append({
        "tasks": json.loads(json.dumps(data["tasks"])),
        "next_id": data["next_id"],
    })

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


def cmd_list(args):
    """List tasks."""
    data = load_data()
    if not data["tasks"]:
        print("No tasks")
        return

    tasks = list(data["tasks"])

    # Parse arguments
    sort_by_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            i += 1
            if i >= len(args):
                error("Missing sort value")
            if args[i] == "priority":
                sort_by_priority = True
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                error("Missing tag value")
            filter_tag = args[i]
        elif args[i] == "--overdue":
            overdue = True
        elif args[i] == "--today":
            i += 1
            if i >= len(args):
                error("Missing today value")
            today_str = args[i]
        i += 1

    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if overdue:
        today = date.today()
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
        today_iso = today.strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_iso]

    if sort_by_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    if not args:
        error("Missing task id")
    task_id = int(args[0])

    # Find task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["undo_history"].append({
        "tasks": json.loads(json.dumps(data["tasks"])),
        "next_id": data["next_id"],
    })

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    if not args:
        error("Missing task id")
    task_id = int(args[0])

    # Find task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["undo_history"].append({
        "tasks": json.loads(json.dumps(data["tasks"])),
        "next_id": data["next_id"],
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task."""
    data = load_data()
    if not args:
        error("Missing task id")
    task_id = int(args[0])

    # Find task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Parse arguments
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                error("Missing title value")
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        error("Missing --title argument")

    # Save state for undo
    data["undo_history"].append({
        "tasks": json.loads(json.dumps(data["tasks"])),
        "next_id": data["next_id"],
    })

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title."""
    data = load_data()
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    results = [t for t in data["tasks"] if query in t["title"].lower()]

    if not results:
        print("No matches")
        return

    # Sort by id
    results.sort(key=lambda t: t["id"])

    for task in results:
        print(format_task(task))


def cmd_export(args):
    """Export tasks."""
    data = load_data()
    if not args:
        error("Missing --format argument")

    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("Missing format value")
            fmt = args[i]
        i += 1

    if fmt not in ("json", "csv"):
        error(f"Invalid format: {fmt}")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args):
    """Show task statistics."""
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total_count = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()

    if not data["undo_history"]:
        error("Nothing to undo")

    previous = data["undo_history"].pop()
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
