#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Build the display line for a task."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # tags suffix
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Handle 'add' command."""
    data = load_data()
    # Parse args for --priority, --tag, --due
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    new_task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }

    # Save state for undo before mutation
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"].append(new_task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {new_task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    # Parse flags
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    today = date.today()
    if today_str:
        today = datetime.strptime(today_str, "%Y-%m-%d").date()

    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue (open tasks with due date before today)
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    # Sort by id (default) or priority then id
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    """Handle 'done' command."""
    data = load_data()
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    data = load_data()
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    data = load_data()
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Parse --title
    new_title = None
    i = 1
    title_parts = []
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                error("Missing title value")
            # Collect until next flag
            while i < len(args) and args[i].startswith("--") is False:
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        else:
            i += 1

    if new_title is None:
        error("Missing --title")

    # Save state for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    data = load_data()
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    matches = []
    for t in sorted(data["tasks"], key=lambda x: x["id"]):
        if query in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")

    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
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
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
