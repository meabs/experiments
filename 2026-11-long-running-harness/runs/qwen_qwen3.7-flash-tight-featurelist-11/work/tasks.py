#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from the JSON file, or return initial state."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": {}, "next_id": 1, "undo_history": []}


def save_data(data):
    """Save tasks to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def snapshot_undo(data):
    """Capture current state for undo."""
    data["undo_history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    return f"{task['id']} {status} {task['title']}"


def cmd_add(args):
    """Handle 'add' command."""
    if not args:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    title = " ".join(args)
    data = load_data()

    # Snapshot before mutation
    snapshot_undo(data)

    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
    }
    data["next_id"] = task_id + 1

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return

    for tid in sorted(tasks.keys()):
        print(task_line(tasks[tid]))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Snapshot before mutation
    snapshot_undo(data)

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        cmd_add(sys.argv[2:])
    elif command == "list":
        cmd_list(sys.argv[2:])
    elif command == "done":
        cmd_done(sys.argv[2:])
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
