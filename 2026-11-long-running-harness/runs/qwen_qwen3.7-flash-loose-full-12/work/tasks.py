#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks.undo.json"


def load_tasks():
    """Load tasks from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    """Load undo history from file."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(history):
    """Save undo history to file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f' due:{task["due"]}'
    return line


def cmd_add(args, data):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due_str = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("No title provided")

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    save_tasks(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_by = None
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            sort_by = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if today is None:
        today = date.today().isoformat()

    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue: only open tasks with due date before today
    if overdue:
        cutoff = date.fromisoformat(today)
        tasks = [
            t
            for t in tasks
            if not t["done"]
            and t.get("due")
            and date.fromisoformat(t["due"]) < cutoff
        ]

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Usage: done ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    task["done"] = True
    save_tasks(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Usage: delete ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    data["tasks"].remove(task)
    save_tasks(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    task_id = int(args[0])
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
            if i + 1 >= len(args):
                error("Missing value for --title")
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        else:
            i += 1

    if new_title is None:
        error("No --title provided")

    task["title"] = new_title
    save_tasks(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    results = []
    for t in sorted(data["tasks"], key=lambda x: x["id"]):
        if query in t["title"].lower():
            results.append(t)

    if not results:
        print("No matches")
        return

    for t in results:
        print(task_line(t))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Usage: export --format json|csv")

    if fmt not in ("json", "csv"):
        error(f"Invalid format: {fmt}")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    history = load_undo()
    if not history:
        error("Nothing to undo")
    prev_state = history.pop()
    save_undo(history)
    # Restore state
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_tasks(data)
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

    # For commands that record undo history (mutating commands)
    mutating_commands = {"add", "done", "delete", "edit"}

    if command in mutating_commands:
        # Save current state for undo BEFORE executing
        data = load_tasks()
        snapshot = {
            "tasks": list(data["tasks"]),
            "next_id": data["next_id"],
        }
        history = load_undo()
        history.append(snapshot)
        save_undo(history)

    data = load_tasks()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
