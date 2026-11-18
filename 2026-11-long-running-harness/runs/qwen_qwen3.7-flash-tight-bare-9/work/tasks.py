#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import copy
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        if "tasks" not in data:
            data["tasks"] = {}
        if "next_id" not in data:
            data["next_id"] = 1
        if "history" not in data:
            data["history"] = []
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "history": []}


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]

    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium shows no suffix

    # Tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")

    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")

    return " ".join(parts)


def cmd_add(args, data):
    """Add a new task."""
    title = " ".join(args.title)
    priority = args.priority
    tags = list(args.tag) if args.tag else []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate due date
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    next_id = data["next_id"]
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Save state before mutation for undo
    snapshot = {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(snapshot)

    data["tasks"][str(next_id)] = task
    data["next_id"] += 1
    save_data(data)
    print(f"Added {next_id}")


def cmd_list(args, data):
    """List tasks."""
    tasks = list(data["tasks"].values())

    # Filter by tag
    if hasattr(args, "tag") and args.tag:
        tasks = [t for t in tasks if any(tag in t["tags"] for tag in args.tag)]

    # Filter overdue
    if hasattr(args, "overdue") and args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        tasks = [
            t
            for t in tasks
            if not t["done"]
            and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today_date
        ]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if hasattr(args, "sort") and args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    task_id = str(args.id)
    if task_id not in data["tasks"]:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    # Save state before mutation for undo
    snapshot = {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(snapshot)

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {args.id}")


def cmd_delete(args, data):
    """Delete a task."""
    task_id = str(args.id)
    if task_id not in data["tasks"]:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    # Save state before mutation for undo
    snapshot = {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(snapshot)

    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {args.id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    task_id = str(args.id)
    if task_id not in data["tasks"]:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    # Save state before mutation for undo
    snapshot = {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(snapshot)

    data["tasks"][task_id]["title"] = " ".join(args.title)
    save_data(data)
    print(f"Edited {args.id}")


def cmd_search(args, data):
    """Search tasks by title."""
    query = " ".join(args.text).lower()
    matches = [t for t in data["tasks"].values() if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Export tasks."""
    fmt = args.format
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task["tags"],
                "due": task["due"],
            })
        print(json.dumps(export_data, indent=2))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in tasks:
            writer.writerow([
                task["id"],
                task["title"],
                "true" if task["done"] else "false",
                task["priority"],
                ";".join(task["tags"]),
                task["due"] if task["due"] else "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args, data):
    """Print stats."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args, data):
    """Undo the most recent mutating command."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    snapshot = data["history"].pop()
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]
    save_data(data)
    print("Undone")


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", nargs="+", help="Task title")
    add_parser.add_argument("--priority", default="medium", help="Priority (high/medium/low)")
    add_parser.add_argument("--tag", action="append", help="Tag (repeatable)")
    add_parser.add_argument("--due", help="Due date (YYYY-MM-DD)")

    # list
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--tag", action="append", help="Filter by tag")
    list_parser.add_argument("--sort", choices=["priority"], help="Sort order")
    list_parser.add_argument("--overdue", action="store_true", help="Show only overdue tasks")
    list_parser.add_argument("--today", help="Today's date (YYYY-MM-DD, defaults to real date)")

    # done
    done_parser = subparsers.add_parser("done", help="Mark a task as done")
    done_parser.add_argument("id", type=int, help="Task ID")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int, help="Task ID")

    # edit
    edit_parser = subparsers.add_parser("edit", help="Edit a task's title")
    edit_parser.add_argument("id", type=int, help="Task ID")
    edit_parser.add_argument("--title", nargs="+", required=True, help="New title")

    # search
    search_parser = subparsers.add_parser("search", help="Search tasks")
    search_parser.add_argument("text", nargs="+", help="Search text")

    # export
    export_parser = subparsers.add_parser("export", help="Export tasks")
    export_parser.add_argument("--format", required=True, choices=["json", "csv"], help="Export format")

    # stats
    subparsers.add_parser("stats", help="Print stats")

    # undo
    subparsers.add_parser("undo", help="Undo last mutation")

    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    data = load_data()

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

    handler = commands.get(args.command)
    if handler:
        handler(args, data)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
