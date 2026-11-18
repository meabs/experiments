#!/usr/bin/env python3
"""A command-line task manager."""

import argparse
import copy
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_data():
    """Load tasks and history from disk."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"tasks": [], "next_id": 1}
    return data


def save_data(data):
    """Save tasks to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    """Load undo history from disk."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history):
    """Save undo history to disk."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def format_task(task):
    """Format a task into a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args, data, history):
    """Add a new task."""
    title = " ".join(args.title)
    priority = args.priority
    tags = args.tag or []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        error(f"Invalid priority: {priority}")

    # Validate date if provided
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            error(f"Invalid date: {due}")

    # Save state BEFORE mutation for undo
    history.append(copy.deepcopy(data))

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

    save_history(history)
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data, history):
    """List tasks with optional filters."""
    tasks = list(data["tasks"])

    # Filter by tag
    if args.tag:
        tasks = [t for t in tasks if args.tag in t["tags"]]

    # Filter overdue
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [
            t for t in tasks
            if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today
        ]

    # Sort by priority if requested
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(format_task(task))


def cmd_done(args, data, history):
    """Mark a task as done."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation for undo
    history.append(copy.deepcopy(data))

    task["done"] = True

    save_history(history)
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data, history):
    """Delete a task."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation for undo
    history.append(copy.deepcopy(data))

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    save_history(history)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data, history):
    """Edit a task's title."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation for undo
    history.append(copy.deepcopy(data))

    task["title"] = " ".join(args.title)

    save_history(history)
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data, history):
    """Search tasks by title (case-insensitive)."""
    text = args.text.lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task(task))


def cmd_export(args, data, history):
    """Export tasks in JSON or CSV format."""
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(output.getvalue(), end="")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args, data, history):
    """Show task statistics."""
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data, history):
    """Undo the most recent mutating command."""
    if not history:
        error("Nothing to undo")
    previous_state = history.pop()
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
    save_history(history)
    save_data(data)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task Manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=None)
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", choices=["priority"], default=None)
    list_parser.add_argument("--tag", default=None)
    list_parser.add_argument("--overdue", action="store_true")
    list_parser.add_argument("--today", default=None)

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    # delete
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)

    # edit
    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("--title", nargs="+", required=True)

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", required=True, choices=["json", "csv"])

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    data = load_data()
    history = load_history()

    commands = {
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

    cmd_func = commands[args.command]
    cmd_func(args, data, history)


if __name__ == "__main__":
    main()
