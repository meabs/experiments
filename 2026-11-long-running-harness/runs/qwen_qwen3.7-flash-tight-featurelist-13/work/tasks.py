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
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    if task.get("priority"):
        if task["priority"] == "high":
            parts.append("(high)")
        elif task["priority"] == "low":
            parts.append("(low)")
    if task.get("tags"):
        for tag in task["tags"]:
            parts.append(f"#{tag}")
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args, data):
    """Handle 'add' command."""
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value after --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Invalid date: ")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        elif title is None:
            title = args[i]
            i += 1
        else:
            title += " " + args[i]
            i += 1

    if title is None:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    # Save undo snapshot BEFORE mutation
    data["undo_stack"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority if priority != "medium" else None,
        "tags": tags,
        "due": due if due else None,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_option = None
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort option")
            sort_option = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value after --tag")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing date after --today")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter: only open tasks with due date before today
    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
        else:
            today = date.today()
        today_str_normalized = today.strftime("%Y-%m-%d")
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_str_normalized
        ]

    # Sort
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority"), 1), t["id"]))
    elif sort_option:
        error(f"Unknown sort option: {sort_option}")

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save undo snapshot BEFORE mutation
    data["undo_stack"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task["done"] = True

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save undo snapshot BEFORE mutation
    data["undo_stack"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    task_id = None
    new_title = None
    i = 0
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title after --title")
            # Collect rest as title
            new_title = " ".join(args[i + 1:])
            break
        else:
            i += 1

    if task_id is None and args:
        try:
            task_id = int(args[0])
        except ValueError:
            error(f"Invalid task id: {args[0]}")

    if task_id is None:
        error("Usage: edit ID --title NEW TITLE")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save undo snapshot BEFORE mutation
    data["undo_stack"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task["title"] = new_title

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args).lower()

    matches = [t for t in data["tasks"] if text in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    # Sort by id
    matches.sort(key=lambda t: t["id"])
    for t in matches:
        print(task_line(t))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority') or ''},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["undo_stack"]:
        error("Nothing to undo")

    prev = data["undo_stack"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]

    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_data()

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

    commands[command](args, data)


if __name__ == "__main__":
    main()
