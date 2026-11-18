#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", [])
    except (json.JSONDecodeError, KeyError):
        return []


def load_next_id():
    """Load the next_id value from the data file."""
    if not os.path.exists(DATA_FILE):
        return 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return max(data.get("next_id", 1), 1)
    except (json.JSONDecodeError, KeyError):
        return 1


def save_tasks(tasks, next_id=None):
    """Save tasks and optionally an explicit next_id to data file."""
    if next_id is None:
        if tasks:
            current_max = max(t["id"] for t in tasks)
            saved_next = load_next_id()
            next_id_val = max(current_max + 1, saved_next)
        else:
            saved_next = load_next_id()
            next_id_val = max(saved_next, 1)
    else:
        next_id_val = next_id
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id_val}, f, indent=2)


def load_history():
    """Load undo history from history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_history(history):
    """Save undo history to history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_undo(tasks):
    """Push current state onto undo history, including next_id."""
    history = load_history()
    history.append({
        "tasks": list(tasks),
        "next_id": load_next_id(),
    })
    # Keep only last 100 states to avoid unbounded growth
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def undo(args=None):
    """Revert to the previous state."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = history.pop()
    save_history(history)
    save_tasks(prev_state["tasks"], prev_state["next_id"])
    print("Undone")


def parse_date(value):
    """Validate and parse a YYYY-MM-DD date string."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


def format_task(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args):
    """Add a new task."""
    title = " ".join(args.title)
    priority = args.priority or "medium"
    tags = args.tag or []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate date
    if due is not None:
        parsed = parse_date(due)
        if parsed is None:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)
        due = parsed

    tasks = load_tasks()
    push_undo(tasks)

    # Compute next id
    if tasks:
        current_max = max(t["id"] for t in tasks)
    else:
        current_max = 0
    saved_next = load_next_id()
    new_id = max(current_max + 1, saved_next)

    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {new_id}")


def cmd_list(args):
    """List tasks."""
    tasks = load_tasks()

    if not tasks:
        print("No tasks")
        return

    filtered = list(tasks)

    # Filter by tag if specified
    if hasattr(args, "tag") and args.tag:
        tag_filter = set(args.tag)
        filtered = [t for t in filtered if tag_filter & set(t.get("tags", []))]

    # Filter overdue if specified
    if hasattr(args, "overdue") and args.overdue:
        today_str = args.today or date.today().isoformat()
        today = parse_date(today_str)
        if today is None:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and t["due"] < today
        ]

    # Sort
    if hasattr(args, "sort") and args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(format_task(task))


def cmd_done(args):
    """Mark a task as done."""
    task_id = args.id
    tasks = load_tasks()
    push_undo(tasks)

    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks)
            print(f"Done {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Delete a task."""
    task_id = args.id
    tasks = load_tasks()
    push_undo(tasks)

    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            save_tasks(tasks)
            print(f"Deleted {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    """Edit a task's title."""
    task_id = args.id
    new_title = " ".join(args.title)
    tasks = load_tasks()
    push_undo(tasks)

    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            save_tasks(tasks)
            print(f"Edited {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Search tasks by title text."""
    tasks = load_tasks()
    query = args.text.lower()

    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    tasks = load_tasks()
    fmt = args.format

    if fmt == "json":
        export_data = []
        for task in sorted(tasks, key=lambda t: t["id"]):
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(export_data, indent=2))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in sorted(tasks, key=lambda t: t["id"]):
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            writer.writerow([
                task["id"],
                task["title"],
                "true" if task["done"] else "false",
                task.get("priority", "medium"),
                tags_str,
                due_str,
            ])
        print(output.getvalue(), end="")

    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Print task statistics."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def main():
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
    list_parser.add_argument("--sort", choices=["priority"], default=None)
    list_parser.add_argument("--tag", action="append", default=None)
    list_parser.add_argument("--overdue", action="store_true", default=False)
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

    if args.command is None:
        parser.print_help(file=sys.stderr)
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
        "undo": undo,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
