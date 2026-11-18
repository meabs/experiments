#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from the data file, or return empty state."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    """Format a task as a display line."""
    done_marker = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {done_marker} {task['title']}"]

    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")
    # medium shows no suffix

    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        parts.append(f"#{tag}")

    # Due date suffix
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")

    return " ".join(parts)


def cmd_add(args, data):
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
            priority_val = args[i + 1]
            if priority_val not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority_val}")
            priority = priority_val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing date value")
            due_val = args[i + 1]
            try:
                datetime.strptime(due_val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_val}")
            due = due_val
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    # Save state BEFORE mutation
    data["undo_history"].append(json.dumps(data))

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["tasks"].append({
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    })
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_mode = None
    tag_filter = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing date value")
            today = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue
    if overdue:
        if today is None:
            today_str = date.today().isoformat()
        else:
            today_str = today
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Usage: done ID")
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

    # Save state BEFORE mutation
    data["undo_history"].append(json.dumps(data))

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
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation
    data["undo_history"].append(json.dumps(data))

    data["tasks"].remove(task)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")

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

    # Parse --title
    title_parts = []
    i = 1
    found_title = False
    while i < len(args):
        if args[i] == "--title":
            found_title = True
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
        else:
            i += 1

    if not found_title or not title_parts:
        error("Usage: edit ID --title NEW TITLE")

    # Save state BEFORE mutation
    data["undo_history"].append(json.dumps(data))

    new_title = " ".join(title_parts)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Usage: search TEXT")

    text = " ".join(args).lower()
    results = [t for t in data["tasks"] if text in t["title"].lower()]
    results.sort(key=lambda t: t["id"])

    if not results:
        print("No matches")
        return

    for task in results:
        print(format_task_line(task))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Usage: export --format json|csv")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["undo_history"]:
        error("Nothing to undo")

    previous_state = data["undo_history"].pop()
    prev = json.loads(previous_state)
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    data["undo_history"] = prev["undo_history"]
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
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
