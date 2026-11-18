#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    return " ".join(parts)


def cmd_add(args, data):
    """Add a new task."""
    title = None
    for i, arg in enumerate(args):
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            break
        elif arg.startswith("--"):
            continue
        else:
            if title is None:
                title = arg
            else:
                title += " " + arg
    if title is None:
        print("Usage: add TITLE [--priority high|medium|low]", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    prev_state = {
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(prev_state)

    task_id = data["next_id"]
    data["next_id"] += 1
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
    }
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """List tasks."""
    filter_tag = None
    sort_by = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing date value", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if overdue:
        import datetime
        if today is None:
            today = datetime.date.today().isoformat()
        cutoff = datetime.date.fromisoformat(today)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    prev_state = {
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(prev_state)

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    prev_state = {
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(prev_state)

    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    prev_state = {
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(prev_state)

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title substring."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_stats(args, data):
    """Print task statistics."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    data = load_data()

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
        "delete": cmd_delete,
        "edit": cmd_edit,
        "search": cmd_search,
        "stats": cmd_stats,
        "undo": cmd_undo,
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args, data)


if __name__ == "__main__":
    main()
