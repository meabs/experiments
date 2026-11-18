#!/usr/bin/env python3
"""A command-line task manager."""

import json
import sys
import os
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print an error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium has no suffix
    # Tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def push_undo(data, snapshot):
    """Push a snapshot onto the undo stack."""
    data["undo_stack"].append(snapshot)


def do_add(data, args):
    """Handle 'add' command."""
    priority = "medium"
    tags = []
    due = None

    i = 0
    title_parts = []
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("--priority requires a value")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("--due requires a value")
            due = args[i]
            # Validate date
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("add requires a title")

    title = " ".join(title_parts)

    # Save snapshot before mutation
    snapshot = {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }
    push_undo(data, snapshot)

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


def do_list(data, args):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                error("--sort requires a value")
            sort_key = args[i]
            if sort_key == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {sort_key}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            tag_filter = args[i]
        elif arg == "--overdue":
            i += 1
            today_str = None
            if i < len(args) and args[i].startswith("--today"):
                # Parse --today VALUE or --today=VALUE
                if "=" in args[i]:
                    today_str = args[i].split("=", 1)[1]
                else:
                    i += 1
                    if i >= len(args):
                        error("--today requires a value")
                    today_str = args[i]
            elif i < len(args) and not args[i].startswith("--"):
                today_str = args[i]
                i += 1
            else:
                today_str = date.today().isoformat()
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
            overdue_tasks = [
                t for t in data["tasks"]
                if not t["done"] and t.get("due") and t["due"] < today_str
            ]
            if not overdue_tasks:
                print("No matches")
            else:
                for t in overdue_tasks:
                    print(task_line(t))
            return
        else:
            error(f"Unknown option: {arg}")
        i += 1

    tasks = data["tasks"]

    # Apply tag filter
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for t in tasks:
        print(task_line(t))


def do_done(data, args):
    """Handle 'done' command."""
    if not args:
        error("done requires an ID")
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

    # Save snapshot before mutation
    snapshot = {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }
    push_undo(data, snapshot)

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def do_delete(data, args):
    """Handle 'delete' command."""
    if not args:
        error("delete requires an ID")
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

    # Save snapshot before mutation
    snapshot = {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }
    push_undo(data, snapshot)

    data["tasks"].remove(task)
    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(data, args):
    """Handle 'edit' command."""
    if not args:
        error("edit requires an ID")
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
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        error("edit --title requires a new title")

    # Save snapshot before mutation
    snapshot = {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }
    push_undo(data, snapshot)

    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def do_search(data, args):
    """Handle 'search' command."""
    if not args:
        error("search requires TEXT")

    query = " ".join(args).lower()
    matches = []
    for t in data["tasks"]:
        if query in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def do_export(data, args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("--format requires a value")
            fmt = args[i]
        i += 1

    if fmt is None:
        error("export requires --format json or csv")

    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_list = []
        for t in tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_list))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def do_stats(data, args):
    """Handle 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(data, args):
    """Handle 'undo' command."""
    if not data["undo_stack"]:
        error("Nothing to undo")

    snapshot = data["undo_stack"].pop()
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]
    save_data(data)
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
        error("Usage: tasks.py <command> [args]")

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        error(f"Unknown command: {cmd}")

    data = load_data()
    COMMANDS[cmd](data, sys.argv[2:])


if __name__ == "__main__":
    main()
