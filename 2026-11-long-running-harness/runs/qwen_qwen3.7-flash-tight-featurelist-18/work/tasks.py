#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    """Load undo history from the data file."""
    if not os.path.exists("history.json"):
        return []
    with open("history.json", "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to the data file."""
    with open("history.json", "w") as f:
        json.dump(history, f, indent=2)


def record_undo(data):
    """Record current state for undo."""
    history = load_history()
    history.append(json.dumps(data))
    save_history(history)


def undo_last():
    """Revert the most recent mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = json.loads(history.pop())
    save_history(history)
    save_tasks(prev_state)
    print("Undone")


def cmd_add(args):
    """Add a new task."""
    if not args:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    title = " ".join(args)
    data = load_tasks()
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": "medium",
        "tags": [],
        "due": None,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    # Record before saving for undo
    record_undo(data)
    save_tasks(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """List tasks."""
    data = load_tasks()
    if not data["tasks"]:
        print("No tasks")
        return

    sort_mode = None
    tag_filter = None
    show_overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            show_overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = data["tasks"]

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if show_overdue:
        if today is None:
            import datetime
            today = datetime.date.today().isoformat()
        overdue_tasks = []
        for t in tasks:
            if not t["done"] and t.get("due"):
                if t["due"] < today:
                    overdue_tasks.append(t)
        tasks = overdue_tasks

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        line = format_task_line(task)
        print(line)


def format_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{tag}" for tag in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    task["done"] = True
    record_undo(data)
    save_tasks(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    record_undo(data)
    save_tasks(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Parse --title
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            new_title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
            task["title"] = " ".join(new_title_parts)
            break
        i += 1

    record_undo(data)
    save_tasks(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    data = load_tasks()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in sorted(matches, key=lambda t: t["id"]):
        print(format_task_line(task))


def cmd_export(args):
    """Export tasks."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
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
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Print stats."""
    data = load_tasks()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": lambda args: undo_last(),
}


def main():
    if not sys.argv[1:]:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
