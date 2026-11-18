#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_history": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "undo_history": []}


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args, data):
    """Add a new task."""
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = task_id + 1

    # Save undo state before mutating
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """List tasks."""
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            if sort_by not in ("priority",):
                print(f"Unknown sort option: {sort_by}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if overdue:
        if today_str is None:
            today_str = datetime.now().strftime("%Y-%m-%d")
        filtered = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    else:
        filtered = tasks

    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    if sort_by == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args or not args[0].isdigit():
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save undo state
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args or not args[0].isdigit():
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save undo state
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args or not args[0].isdigit():
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            if not parts:
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts.extend(parts)
        else:
            i += 1

    if not title_parts:
        print("--title requires a value", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(title_parts)

    # Save undo state
    data["undo_history"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }))

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Unknown format: {fmt}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

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
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Print task statistics."""
    open_count = sum(1 for t in data["tasks"].values() if not t["done"])
    done_count = sum(1 for t in data["tasks"].values() if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = json.loads(data["undo_history"].pop())
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_data()

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
