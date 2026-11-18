#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import copy
import csv
import io
import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks.undo.json"


def load_data():
    """Load tasks from data file, creating if necessary."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1}


def save_data(data):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    """Load undo history from file."""
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo_history(history):
    """Save undo history to file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(state, history):
    """Push current state onto undo history."""
    # Keep last 100 entries
    history.append(copy.deepcopy(state))
    if len(history) > 100:
        history.pop(0)
    save_undo_history(history)


def undo_action(data, history):
    """Revert to the previous state from undo history."""
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = history.pop()
    save_undo_history(history)
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")


def validate_date(date_str):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    """Handle the 'add' command."""
    title = " ".join(args.title)
    priority = getattr(args, "priority", None) or "medium"
    tags = getattr(args, "tag", []) or []
    due = getattr(args, "due", None) or None

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate date
    if due is not None:
        if not validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

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


def cmd_list(args, data):
    """Handle the 'list' command."""
    tasks = data["tasks"]

    # Filter by tag
    if hasattr(args, "tag") and args.tag:
        filter_tag = args.tag[0]
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filter
    if getattr(args, "overdue", False):
        today_str = getattr(args, "today", None)
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        tasks = [
            t
            for t in tasks
            if not t["done"]
            and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    # Sort by priority if requested
    if getattr(args, "sort", None) == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    # Otherwise sort by id
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Handle the 'done' command."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle the 'delete' command."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle the 'edit' command."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(args.title)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle the 'search' command."""
    text = " ".join(args.text).lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Handle the 'export' command."""
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
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
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
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")


def cmd_stats(args, data):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default=None)
    add_parser.add_argument("--tag", action="append", default=None)
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", default=None)
    list_parser.add_argument("--tag", default=None)
    list_parser.add_argument("--overdue", action="store_true", default=False)
    list_parser.add_argument("--today", default=None)

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    # delete
    del_parser = subparsers.add_parser("delete")
    del_parser.add_argument("id", type=int)

    # edit
    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("--title", nargs="+")

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text", nargs="+")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", required=True, choices=["json", "csv"])

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    return parser


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Load data
    data = load_data()

    # Handle undo separately - it doesn't need mutation tracking
    if args.command == "undo":
        history = load_undo_history()
        undo_action(data, history)
        return

    # Get the handler
    handler = COMMANDS.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)

    # For mutating commands, push state before modification
    if args.command in ("add", "done", "delete", "edit"):
        history = load_undo_history()
        push_undo(data, history)

    # Execute the command
    handler(args, data)


if __name__ == "__main__":
    main()
