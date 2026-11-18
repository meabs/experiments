#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import re
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = ".tasks_history.json"


def load_data():
    """Load tasks and next_id from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and next_id to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    """Load undo history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # priority suffix
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    # medium shows no suffix
    # tags suffix
    for tag in task["tags"]:
        parts.append(f"#{tag}")
    # due date suffix
    if task["due"]:
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def do_add(args):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing due date")
            due = args[i + 1]
            # Validate date
            try:
                date.fromisoformat(due)
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    data = load_data()
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

    # Save undo history state before mutation
    history = load_history()
    history.append({"data": _serialize_for_undo(data)})
    save_history(history)

    save_data(data)
    print(f"Added {task['id']}")


def _serialize_for_undo(data):
    """Create a deep copy of data for undo history."""
    return json.loads(json.dumps(data))


def do_list(args):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
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

    data = load_data()
    tasks = data["tasks"]

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    # Filter overdue (only open tasks with due date before today)
    if overdue:
        if today_str:
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                error(f"Invalid date: {today_str}")
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today.isoformat()]

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def do_done(args):
    """Handle 'done' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    task["done"] = True

    # Save undo history
    history = load_history()
    history.append({"data": _serialize_for_undo(data)})
    save_history(history)

    save_data(data)
    print(f"Done {task_id}")


def do_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    # Save undo history
    history = load_history()
    history.append({"data": _serialize_for_undo(data)})
    save_history(history)

    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing new title")
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        error("Missing --title argument")

    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    task["title"] = new_title

    # Save undo history
    history = load_history()
    history.append({"data": _serialize_for_undo(data)})
    save_history(history)

    save_data(data)
    print(f"Edited {task_id}")


def do_search(args):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()

    data = load_data()
    matches = []
    for t in data["tasks"]:
        if query in t["title"].lower():
            matches.append(t)

    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def do_export(args):
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
        error(f"Unknown format: {fmt}")

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def do_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(args):
    """Handle 'undo' command."""
    history = load_history()
    if not history:
        error("Nothing to undo")

    # Pop the last state
    prev_state = history.pop()
    save_history(history)

    # Restore the previous data state
    restored_data = prev_state["data"]
    save_data(restored_data)
    print("Undone")


COMMANDS = {
    "add": do_add,
    "list": do_list,
    "done": do_done,
    "delete": do_delete,
    "edit": do_edit,
    "search": do_search,
    "export": do_export,
    "stats": do_stats,
    "undo": do_undo,
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
