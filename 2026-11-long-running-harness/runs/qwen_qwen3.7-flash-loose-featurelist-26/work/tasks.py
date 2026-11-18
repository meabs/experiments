#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from the JSON file. Returns (tasks_dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", {}), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    """Save tasks and next_id to the JSON file."""
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    return f'{task["id"]} {status} {task["title"]}'


def cmd_add(args):
    """Handle the 'add' command."""
    if not args:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(args)
    tasks, next_id = load_tasks()
    task_id = next_id
    tasks[task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
    }
    save_tasks(tasks, next_id + 1)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle the 'list' command."""
    tasks, _ = load_tasks()
    task_list = sorted(tasks.values(), key=lambda t: t["id"])
    if not task_list:
        print("No tasks")
        return
    for task in task_list:
        print(task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    if not args:
        print("Error: missing id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid id '{args[0]}'", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        print("Error: missing id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid id '{args[0]}'", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        cmd_add(sys.argv[2:])
    elif command == "list":
        cmd_list(sys.argv[2:])
    elif command == "done":
        cmd_done(sys.argv[2:])
    elif command == "delete":
        cmd_delete(sys.argv[2:])
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
