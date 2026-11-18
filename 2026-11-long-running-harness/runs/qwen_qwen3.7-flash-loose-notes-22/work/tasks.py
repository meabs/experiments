#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
import copy
from datetime import date, datetime

TASKS_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    """Load tasks from tasks.json."""
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_tasks(tasks):
    """Save tasks to tasks.json."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo_history():
    """Load undo history from undo.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo_history(history):
    """Save undo history to undo.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def next_id(tasks):
    """Get the next available id (max + 1, or 1 if empty)."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Handle the add command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)
    tasks = load_tasks()

    # Save state for undo BEFORE modifying
    history = load_undo_history()
    history.append(copy.deepcopy(tasks))
    save_undo_history(history)

    task = {
        "id": next_id(tasks),
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the list command."""
    tasks = load_tasks()
    sort_mode = None
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            sort_mode = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing today date")
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            error(f"Unknown option: {arg}")

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue:
        today = date.today().isoformat() if today_str is None else today_str
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort
    if sort_mode == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(args):
    """Handle the done command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks = load_tasks()

    found_task = None
    for t in tasks:
        if t["id"] == tid:
            found_task = t
            break

    if not found_task:
        error(f"No such task: {tid}")

    # Save state for undo BEFORE modifying
    history = load_undo_history()
    history.append(copy.deepcopy(tasks))
    save_undo_history(history)

    found_task["done"] = True
    save_tasks(tasks)
    print(f"Done {tid}")


def cmd_delete(args):
    """Handle the delete command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks = load_tasks()

    found = False
    new_tasks = []
    for t in tasks:
        if t["id"] == tid:
            found = True
        else:
            new_tasks.append(t)

    if not found:
        error(f"No such task: {tid}")

    # Save state for undo BEFORE modifying
    history = load_undo_history()
    history.append(copy.deepcopy(tasks))
    save_undo_history(history)

    save_tasks(new_tasks)
    print(f"Deleted {tid}")


def cmd_edit(args):
    """Handle the edit command."""
    tid = None
    new_title = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            new_title = args[i + 1]
            i += 2
        else:
            if tid is None:
                try:
                    tid = int(arg)
                except ValueError:
                    error(f"Invalid task id: {arg}")
            else:
                error(f"Unknown option: {arg}")
            i += 1

    if tid is None:
        error("Missing task id")
    if new_title is None:
        error("Missing --title")

    tasks = load_tasks()

    found_task = None
    for t in tasks:
        if t["id"] == tid:
            found_task = t
            break

    if not found_task:
        error(f"No such task: {tid}")

    # Save state for undo BEFORE modifying
    history = load_undo_history()
    history.append(copy.deepcopy(tasks))
    save_undo_history(history)

    found_task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {tid}")


def cmd_search(args):
    """Handle the search command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
    else:
        matches.sort(key=lambda t: t["id"])
        for t in matches:
            print(task_line(t))


def cmd_export(args):
    """Handle the export command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    if fmt is None:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f'{t["id"]},{t["title"]},{"true" if t["done"] else "false"},{t.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(args):
    """Handle the stats command."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the undo command."""
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    previous = history.pop()
    save_undo_history(history)
    save_tasks(previous)
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
