#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    """Load tasks data from JSON file. Return default if file doesn't exist."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    """Load undo history from JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to JSON file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def format_task_line(task):
    """Format a task as a display line."""
    check = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {check} {task['title']}"
    # Priority suffix (high/low only, medium shows nothing)
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # Tags suffix (after priority)
    if task["tags"]:
        tag_str = " ".join(f"#{t}" for t in task["tags"])
        line += f" {tag_str}"
    # Due date suffix (after tags)
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def push_undo(data):
    """Push current state onto undo stack."""
    history = load_history()
    history.append(json.dumps(data))
    save_history(history)


def do_add(args):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            i += 1
            if i >= len(args):
                error("Invalid priority: ")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                error("Missing tag value")
            tags.append(args[i])
        elif args[i] == "--due":
            i += 1
            if i >= len(args):
                error("Missing due date")
            due = args[i]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
        else:
            title_parts.append(args[i])
        i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]")

    title = " ".join(title_parts)
    data = load_data()
    push_undo(data)
    new_id = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {new_id}")


def do_list(args):
    """Handle 'list' command."""
    sort_by = None
    filter_tag = None
    overdue = False
    today_val = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            i += 1
            if i >= len(args):
                error("Missing sort value")
            sort_by = args[i]
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                error("Missing tag value")
            filter_tag = args[i]
        elif args[i] == "--overdue":
            overdue = True
        elif args[i] == "--today":
            i += 1
            if i >= len(args):
                error("Missing date value")
            today_val = args[i]
        i += 1

    data = load_data()
    tasks = list(data["tasks"])

    if overdue:
        if today_val:
            try:
                today = datetime.strptime(today_val, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_val}")
        else:
            today = date.today()
        today_str = str(today)
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_str]

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(format_task_line(t))


def do_done(args):
    """Handle 'done' command."""
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Usage: done ID")
    data = load_data()
    push_undo(data)
    found = False
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            found = True
            break
    if not found:
        error(f"No such task: {task_id}")
    save_data(data)
    print(f"Done {task_id}")


def do_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Usage: delete ID")
    data = load_data()
    push_undo(data)
    found = False
    new_tasks = []
    for t in data["tasks"]:
        if t["id"] == task_id:
            found = True
        else:
            new_tasks.append(t)
    if not found:
        error(f"No such task: {task_id}")
    data["tasks"] = new_tasks
    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Usage: edit ID")
    data = load_data()
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                error("Missing title")
            # Collect all remaining args as the title
            parts = []
            while i < len(args):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1

    if new_title is None:
        error("Usage: edit ID --title NEW TITLE")

    found = False
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["title"] = new_title
            found = True
            break
    if not found:
        error(f"No such task: {task_id}")

    push_undo(data)
    save_data(data)
    print(f"Edited {task_id}")


def do_search(args):
    """Handle 'search' command."""
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    data = load_data()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task_line(t))


def do_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("Missing format value")
            fmt = args[i]
        i += 1

    if not fmt:
        error("Usage: export --format json|csv")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            done_str = "true" if t["done"] else "false"
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
    history.pop()
    save_history(history)
    # Restore previous state
    if history:
        prev_state = json.loads(history[-1])
    else:
        prev_state = {"tasks": [], "next_id": 1}
    save_data(prev_state)
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
    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
