#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and next_id from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and next_id to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    return f'{task["id"]} [{status}] {task["title"]}'


def cmd_add(args):
    """Handle 'add' command."""
    if not args:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task_id = data["next_id"]
    task = {"id": task_id, "title": " ".join(args), "done": False}
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command == "add":
        cmd_add(args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
