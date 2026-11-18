#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if "undo_stack" not in data:
        data["undo_stack"] = []
    return data


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task into its display line."""
    done_mark = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), done_mark, task["title"]]
    # Priority suffix
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    # Tags suffix
    for tag in task["tags"]:
        parts.append(f"#{tag}")
    # Due date suffix
    if task["due"]:
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args):
    """Handle 'add' command."""
    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("Missing value for --priority")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing value for --tag")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("Missing value for --due")
            due_val = args[i]
            try:
                datetime.strptime(due_val, "%Y-%m-%d")
                due = due_val
            except ValueError:
                error(f"Invalid date: {due_val}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Record state before mutation for undo
    data["undo_stack"].append({
        "action": "add",
        "state": {
            "tasks": list(data["tasks"]),
            "next_id": data["next_id"],
        }
    })

    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    sort_by = None
    filter_tag = None
    overdue = False
    today_str = None
    today = date.today().isoformat()

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                error("Missing value for --sort")
            sort_by = args[i]
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("Missing value for --tag")
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                error("Missing value for --today")
            today_str = args[i]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
                today = today_str
            except ValueError:
                error(f"Invalid date: {today_str}")
        i += 1

    tasks = data["tasks"]

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    # Filter overdue (open tasks due before today)
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


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

    # Record state before mutation
    data["undo_stack"].append({
        "action": "done",
        "state": {
            "tasks": list(data["tasks"]),
            "next_id": data["next_id"],
        },
        "task_id": task_id,
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

    # Record state before mutation
    data["undo_stack"].append({
        "action": "delete",
        "state": {
            "tasks": list(data["tasks"]),
            "next_id": data["next_id"],
        },
        "task_id": task_id,
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

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                error("Missing value for --title")
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            if not title_parts:
                error("Missing title value")
            new_title = " ".join(title_parts)
            continue
        i += 1

    if new_title is None:
        error("Missing --title option")

    # Record state before mutation
    data["undo_stack"].append({
        "action": "edit",
        "state": {
            "tasks": list(data["tasks"]),
            "next_id": data["next_id"],
        },
        "task_id": task_id,
        "old_title": task["title"],
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
    for task in data["tasks"]:
        if query in task["title"].lower():
            matches.append(task)

    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("Missing format value")
            fmt = args[i]
        i += 1

    if fmt is None:
        error("Missing --format option")

    if fmt == "json":
        export_tasks = sorted(data["tasks"], key=lambda t: t["id"])
        result = []
        for t in export_tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        export_tasks = sorted(data["tasks"], key=lambda t: t["id"])
        print("id,title,done,priority,tags,due")
        for t in export_tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f'{t["id"]},{t["title"]},{done_str},{t["priority"]},{tags_str},{due_str}')
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()
    if not data["undo_stack"]:
        error("Nothing to undo")

    entry = data["undo_stack"].pop()
    state = entry["state"]
    data["tasks"] = state["tasks"]
    data["next_id"] = state["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

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
        error(f"Unknown command: {command}")

    commands[command](args)


if __name__ == "__main__":
    main()
