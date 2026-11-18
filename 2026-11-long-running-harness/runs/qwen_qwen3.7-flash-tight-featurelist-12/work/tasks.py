#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from the data file. Returns (tasks_dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", {}), data.get("next_id", 1)


def save_data(tasks, next_id):
    """Save tasks to the data file."""
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def cmd_add(args):
    """Handle the 'add' command."""
    if len(args) == 0:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)
    title = " ".join(args)
    tasks, next_id = load_data()
    task_id = next_id
    tasks[str(task_id)] = {
        "title": title,
        "done": False,
        "priority": "medium",
        "tags": [],
        "due": None,
    }
    save_data(tasks, next_id + 1)
    print(f"Added {task_id}")


def task_line(task):
    """Format a single task line."""
    status = "x" if task["done"] else " "
    parts = [f'{int(task["id"])} [{status}] {task["title"]}']
    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        parts.extend(tags)
    # Due date suffix
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def cmd_list(args):
    """Handle the 'list' command."""
    tasks, next_id = load_data()
    sorted_ids = sorted(tasks.keys(), key=lambda x: int(x))
    if not sorted_ids:
        print("No tasks")
        return
    for tid in sorted_ids:
        task = tasks[tid]
        task["id"] = int(tid)
        print(task_line(task))


def cmd_done(args):
    """Handle the 'done' command - marks a task as done."""
    if len(args) != 1:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_data()
    if str(task_id) not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    tasks[str(task_id)]["done"] = True
    save_data(tasks, next_id)
    print(f"Done {task_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
    }
    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    commands[command](args)


if __name__ == "__main__":
    main()
