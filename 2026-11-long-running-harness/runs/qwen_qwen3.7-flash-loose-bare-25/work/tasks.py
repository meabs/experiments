#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import calendar
import copy
import csv
import io
import json
import os
import re
import sys


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    """Load tasks from the data file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_history():
    """Load undo history from the history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to the history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_undo(tasks, max_id):
    """Push current state onto undo stack."""
    history = load_history()
    history.append({"tasks": copy.deepcopy(tasks), "max_id": max_id})
    # Keep only last 100 entries to avoid unbounded growth
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def do_undo():
    """Revert to previous state. Returns (tasks, max_id) or None on error."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        return None
    entry = history.pop()
    save_history(history)
    return entry["tasks"], entry["max_id"]


def next_id(tasks, max_id):
    """Return the next available task id (max_id + 1, starting at 1)."""
    if max_id is None:
        return 1
    return max_id + 1


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")
    # Tags suffix
    if task.get("tags"):
        parts.extend("#" + tag for tag in task["tags"])
    # Due date suffix
    if task.get("due"):
        parts.append("due:" + task["due"])
    return " ".join(parts)


def valid_date(date_str):
    """Check if a date string is valid YYYY-MM-DD format."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        parts = date_str.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        max_day = calendar.monthrange(year, month)[1]
        if day > max_day:
            return False
        return True
    except ValueError:
        return False


def _today_str():
    """Return today's date as YYYY-MM-DD."""
    from datetime import date
    return date.today().isoformat()


def cmd_add(args, tasks, max_id):
    """Handle the 'add' command."""
    title = " ".join(args.title)
    priority = args.priority if args.priority else "medium"
    tags = args.tag if args.tag else []
    due = args.due

    # Validate priority
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate due date
    if due:
        if not valid_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    push_undo(tasks, max_id)

    task = {
        "id": next_id(tasks, max_id),
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    new_max_id = task["id"]
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {task['id']}")
    return new_max_id


def cmd_list(args, tasks):
    """Handle the 'list' command."""
    filtered = list(tasks)

    # Filter by tag if specified
    if args.tag:
        filtered = [t for t in filtered if any(tag in t.get("tags", []) for tag in args.tag)]

    # Filter overdue if --overdue flag is set
    if getattr(args, "overdue", False):
        today = args.today if args.today else _today_str()
        filtered = [t for t in filtered if not t["done"] and t.get("due") and t["due"] < today]

    if not filtered:
        print("No tasks")
        return

    # Sort by priority if requested
    if getattr(args, "sort", None) == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for task in filtered:
        print(task_line(task))


def cmd_done(args, tasks, max_id):
    """Handle the 'done' command."""
    task_id = args.id
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, max_id)
    task["done"] = True
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args, tasks, max_id):
    """Handle the 'delete' command."""
    task_id = args.id
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, max_id)
    tasks[:] = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args, tasks, max_id):
    """Handle the 'edit' command."""
    task_id = args.id
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, max_id)
    if args.title is not None:
        task["title"] = " ".join(args.title)
    if args.priority is not None:
        if args.priority not in ("high", "medium", "low"):
            print(f"Invalid priority: {args.priority}", file=sys.stderr)
            sys.exit(1)
        task["priority"] = args.priority
    if args.due is not None:
        if not valid_date(args.due):
            print(f"Invalid date: {args.due}", file=sys.stderr)
            sys.exit(1)
        task["due"] = args.due
    if args.tags is not None:
        task["tags"] = args.tags
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args, tasks):
    """Handle the 'search' command."""
    query = args.text.lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args, tasks):
    """Handle the 'export' command."""
    fmt = args.format
    tasks_sorted = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks_sorted:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks_sorted:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")


def cmd_stats(args, tasks):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, tasks, max_id):
    """Handle the 'undo' command."""
    result = do_undo()
    if result is None:
        sys.exit(1)
    new_tasks, new_max_id = result
    tasks[:] = new_tasks
    save_tasks(new_tasks)
    print("Undone")
    return new_max_id


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
    list_parser.add_argument("--tag", action="append", default=None)
    list_parser.add_argument("--overdue", action="store_true")
    list_parser.add_argument("--today", default=None)
    list_parser.add_argument("--sort", default=None)

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    # delete
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)

    # edit
    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("--title", nargs="+", default=None)
    edit_parser.add_argument("--priority", default=None)
    edit_parser.add_argument("--due", default=None)
    edit_parser.add_argument("--tags", action="append", default=None)

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", required=True)

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    max_id = None
    if tasks:
        max_id = max(t["id"] for t in tasks)

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
        # Commands that modify state take 3 args (args, tasks, max_id)
        # Read-only commands take 2 args (args, tasks)
        if args.command in ("add", "done", "delete", "edit", "undo"):
            result = handler(args, tasks, max_id)
            if result is not None:
                max_id = result
        else:
            handler(args, tasks)
    else:
        parser.print_help(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
