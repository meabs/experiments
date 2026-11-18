#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def push_undo(data):
    """Push current state onto undo history."""
    data["undo_history"].append(
        {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    )


def cmd_add(args, data):
    """Add a new task."""
    priority = "medium"
    tags = []
    due = None
    positional = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing due value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                parts = due_str.split("-")
                if len(parts) != 3:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, IndexError):
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            positional.append(arg)
            i += 1

    if not positional:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(positional)

    push_undo(data)

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


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def cmd_list(args, data):
    """List tasks with optional filtering and sorting."""
    sort_mode = None
    filter_tag = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("Missing today value", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue:
        if today is None:
            today = date.today().isoformat()
        try:
            parts = today.split("-")
            today_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            print(f"Invalid date: {today}", file=sys.stderr)
            sys.exit(1)

    tasks = data["tasks"]

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today_date]

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args or not args[0].isdigit():
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    tid = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args or not args[0].isdigit():
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    tid = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args or not args[0].isdigit():
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    tid = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    i = 1
    new_title = None
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            # Collect all remaining positional args as the new title
            positional = []
            j = i + 1
            while j < len(args):
                if args[j].startswith("--"):
                    break
                positional.append(args[j])
                j += 1
            if not positional:
                print("Missing --title value", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(positional)
            break
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Search tasks by title substring."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

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
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Print statistics about tasks."""
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["undo_history"].pop()
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
