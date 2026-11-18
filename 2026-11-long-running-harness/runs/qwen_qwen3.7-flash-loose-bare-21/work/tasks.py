#!/usr/bin/env python3
"""A command-line task manager."""

import copy
import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from JSON file, or return initial state."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    """Save tasks data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix (only non-medium)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_add_args(args):
    """Parse arguments for the add command."""
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
            due_str = args[i + 1]
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
        error("Missing title")
    title = " ".join(title_parts)
    return title, priority, tags, due


def parse_list_args(args):
    """Parse arguments for the list command."""
    sort_mode = None
    filter_tag = None
    overdue = False
    today = None
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
                error("Missing today value")
            today = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")
    if overdue and today is None:
        today = date.today().isoformat()
    return sort_mode, filter_tag, overdue, today


def parse_edit_args(args):
    """Parse arguments for the edit command."""
    new_title = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            error(f"Unknown option: {arg}")
    if new_title is None:
        error("Missing --title")
    return new_title


def cmd_add(data, args):
    """Handle the 'add' command."""
    title, priority, tags, due = parse_add_args(args)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    # Save current state to history before mutating
    data["history"].append(copy.deepcopy(data))
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(data, args):
    """Handle the 'list' command."""
    sort_mode, filter_tag, overdue, today = parse_list_args(args)

    tasks = list(data["tasks"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue:
        if today is None:
            today = date.today().isoformat()
        tasks = [t for t in tasks if t.get("due") and t["due"] < today and not t["done"]]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(data, args):
    """Handle the 'done' command."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    data["history"].append(copy.deepcopy(data))
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(data, args):
    """Handle the 'delete' command."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    data["history"].append(copy.deepcopy(data))
    data["tasks"].remove(task)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(data, args):
    """Handle the 'edit' command."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    new_title = parse_edit_args(args[1:])
    data["history"].append(copy.deepcopy(data))
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(data, args):
    """Handle the 'search' command."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(data, args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")
    if fmt is None:
        error("Missing --format")
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
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            lines.append(f"{t['id']},{t['title']},{done_str},{t.get('priority','medium')},{tags_str},{due_str}")
        print("\n".join(lines))


def cmd_stats(data, args):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(data, args):
    """Handle the 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")
    previous = data["history"].pop()
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
    data = load_data()
    COMMANDS[command](data, sys.argv[2:])


if __name__ == "__main__":
    main()
