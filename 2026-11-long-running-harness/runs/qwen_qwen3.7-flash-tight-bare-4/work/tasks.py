#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
import copy
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    data = {
        "tasks": {int(k): v for k, v in raw.get("tasks", {}).items()},
        "next_id": int(raw.get("next_id", 1)),
        "undo_stack": raw.get("undo_stack", []),
    }
    return data


def save_data(data):
    """Persist tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    parts = [f"{task['id']} [{status}] {task['title']}"]
    # Priority suffix
    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        parts.extend(f"#{t}" for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def error(msg):
    """Print error to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def find_task(data, task_id):
    """Find a task by id, or error if not found."""
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")
    return data["tasks"][task_id]


def push_undo(data):
    """Save current state onto the undo stack."""
    data["undo_stack"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))


def cmd_add(args):
    """Handle the add command."""
    data = load_data()
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]")

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
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            val = args[i + 1]
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {val}")
            due = val
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    push_undo(data)
    task_id = data["next_id"]
    data["next_id"] += 1
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle the list command."""
    data = load_data()

    sort_priority = False
    tag_filter = None
    overdue = False
    today = date.today().isoformat()

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
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
            error(f"Unknown option: {arg}")

    tasks = list(data["tasks"].values())

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if not tasks:
        print("No tasks")
        return

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    """Handle the done command."""
    data = load_data()
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = find_task(data, task_id)
    push_undo(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the delete command."""
    data = load_data()
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = find_task(data, task_id)
    push_undo(data)
    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the edit command."""
    data = load_data()
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = find_task(data, task_id)
    # Parse --title flag
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            i += 1
            # Collect all remaining args as the new title
            new_title_parts = args[i:]
            break
        else:
            error(f"Unknown option: {args[i]}")
    if not new_title_parts:
        error("Missing new title")
    new_title = " ".join(new_title_parts)
    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the search command."""
    data = load_data()
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    tasks = [t for t in data["tasks"].values() if query in t["title"].lower()]
    if not tasks:
        print("No matches")
        return
    tasks.sort(key=lambda t: t["id"])
    for t in tasks:
        print(task_line(t))


def cmd_export(args):
    """Handle the export command."""
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if fmt is None:
        error("Usage: export --format json|csv")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

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
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle the stats command."""
    data = load_data()
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args):
    """Handle the undo command."""
    data = load_data()
    if not data["undo_stack"]:
        error("Nothing to undo")
    prev = data["undo_stack"].pop()
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
    cmd_name = sys.argv[1]
    if cmd_name not in COMMANDS:
        error(f"Unknown command: {cmd_name}")
    cmd_args = sys.argv[2:]
    COMMANDS[cmd_name](cmd_args)


if __name__ == "__main__":
    main()
