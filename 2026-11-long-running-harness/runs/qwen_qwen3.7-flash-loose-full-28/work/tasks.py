#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        # Convert string keys back to integers (JSON only supports string keys)
        if "tasks" in data and isinstance(data["tasks"], dict):
            data["tasks"] = {int(k): v for k, v in data["tasks"].items()}
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "history": []}


def save_tasks(data):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    return f"{task['id']} {status} {task['title']}"


def cmd_add(args, data):
    """Add a new task."""
    if not args:
        print("Error: add requires a TITLE", file=sys.stderr)
        sys.exit(1)

    title = " ".join(args)
    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
    }
    data["next_id"] += 1
    # Record history for undo
    data["history"].append({
        "action": "add",
        "task_id": task_id,
        "prev_next_id": data["next_id"] - 1,
    })
    save_tasks(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """List tasks."""
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        print("Error: done requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    old_state = data["tasks"][task_id].copy()
    data["tasks"][task_id]["done"] = True
    data["history"].append({
        "action": "done",
        "task_id": task_id,
        "prev_state": old_state,
    })
    save_tasks(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        print("Error: delete requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    deleted_task = data["tasks"].pop(task_id)
    data["history"].append({
        "action": "delete",
        "task_id": task_id,
        "deleted_task": deleted_task,
        "prev_next_id": data["next_id"],
    })
    save_tasks(data)
    print(f"Deleted {task_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]
    data = load_tasks()

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
        "delete": cmd_delete,
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args, data)


if __name__ == "__main__":
    main()
