#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_tasks(tasks):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo_history():
    """Load undo history from file."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo_history(history):
    """Save undo history to file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(tasks):
    """Push current state onto undo stack."""
    history = load_undo_history()
    history.append(list(tasks))
    save_undo_history(history)


def pop_undo():
    """Pop the most recent state from the undo stack and return it."""
    history = load_undo_history()
    if not history:
        return None
    state = history.pop()
    save_undo_history(history)
    return state


def next_id(tasks):
    """Calculate the next available task id."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"

    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # medium shows no suffix

    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        line += f" #{tag}"

    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"

    return line


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Handle the 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires an argument")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires an argument")
            due_val = args[i + 1]
            try:
                datetime.strptime(due_val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_val}")
            due = due_val
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(title_parts)

    tasks = load_tasks()
    push_undo(tasks)

    new_task = {
        "id": next_id(tasks),
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added {new_task['id']}")


def cmd_list(args):
    """Handle the 'list' command."""
    tasks = load_tasks()
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort_priority = True
            i += 2
        elif arg == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue:
        if today_str is None:
            today_str = date.today().isoformat()
        try:
            datetime.strptime(today_str, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {today_str}")

    filtered = list(tasks)

    if filter_tag is not None:
        filtered = [t for t in filtered if filter_tag in t.get("tags", [])]

    if overdue:
        today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and datetime.strptime(t["due"], "%Y-%m-%d").date() < today_date
        ]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    push_undo(tasks)

    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            break

    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    push_undo(tasks)

    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    # Parse --title
    title_idx = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_idx = i
            break

    if title_idx is None or title_idx + 1 >= len(args):
        error("Usage: edit ID --title NEW TITLE")

    new_title = " ".join(args[title_idx + 1:])

    push_undo(tasks)

    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            break

    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        error("Usage: search TEXT")

    text = " ".join(args).lower()
    tasks = load_tasks()

    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")

    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{str(t["done"]).lower()},{t.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(args):
    """Handle the 'stats' command."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    state = pop_undo()
    if state is None:
        error("Nothing to undo")
    save_tasks(state)
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
