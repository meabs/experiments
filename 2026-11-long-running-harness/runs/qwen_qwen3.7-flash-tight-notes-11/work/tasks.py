#!/usr/bin/env python3
"""A command-line task manager."""

import argparse
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def save_state(data):
    """Push current state onto undo history."""
    snapshot = {
        "tasks": data["tasks"],
        "next_id": data["next_id"],
    }
    data["undo_history"].append(snapshot)


def cmd_add(args):
    """Add a new task."""
    # Join title words into a single string
    title = " ".join(args.title)
    priority = getattr(args, "priority", None) or "medium"
    tags = list(getattr(args, "tag", []) or [])
    due = getattr(args, "due", None) or None

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

    data = load_data()
    save_state(data)

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


def task_line(task):
    """Format a task as a line for list/search output."""
    check = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {check} {task['title']}"]
    # Priority suffix (only high or low)
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # Tags suffix
    if task.get("tags"):
        tag_str = " ".join(f"#{t}" for t in task["tags"])
        parts.append(tag_str)
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_list(args):
    """List tasks with optional filters/sorting."""
    data = load_data()
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return

    result = list(tasks)

    # Filter by tag
    if hasattr(args, "tag") and args.tag:
        result = [t for t in result if args.tag[0] in t.get("tags", [])]

    # Overdue / today filter
    if hasattr(args, "overdue") and args.overdue:
        today_str = getattr(args, "today", None)
        if today_str:
            today = today_str
        else:
            today = date.today().isoformat()
        result = [
            t for t in result
            if not t["done"] and t.get("due") and t["due"] < today
        ]

    # Sort by priority
    if hasattr(args, "sort") and args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        result.sort(key=lambda t: t["id"])

    if not result:
        print("No tasks")
        return

    for task in result:
        print(task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == args.id), None)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)
    save_state(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task['id']}")


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == args.id), None)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)
    save_state(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != args.id]
    save_data(data)
    print(f"Deleted {task['id']}")


def cmd_edit(args):
    """Edit a task's title."""
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == args.id), None)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)
    save_state(data)
    task["title"] = " ".join(args.title)
    save_data(data)
    print(f"Edited {task['id']}")


def cmd_search(args):
    """Search tasks by title (case-insensitive)."""
    data = load_data()
    query = " ".join(args.text).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    data = load_data()
    fmt = getattr(args, "format", "json") or "json"
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        out = []
        for t in tasks:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(out, indent=2))
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(buf.getvalue(), end="")


def cmd_stats(args):
    """Print task statistics."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the most recent mutating command."""
    data = load_data()
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = data["undo_history"].pop()
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
    save_data(data)
    print("Undone")


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority", choices=["high", "medium", "low"])
    p_add.add_argument("--tag", action="append")
    p_add.add_argument("--due")

    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", choices=["priority"])
    p_list.add_argument("--tag", action="append")
    p_list.add_argument("--overdue", action="store_true")
    p_list.add_argument("--today")

    # done
    p_done = subparsers.add_parser("done")
    p_done.add_argument("id", type=int)

    # delete
    p_delete = subparsers.add_parser("delete")
    p_delete.add_argument("id", type=int)

    # edit
    p_edit = subparsers.add_parser("edit")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+")

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("text", nargs="+")

    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("--format", required=True)

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

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
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
