#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import copy
import csv
import datetime
import io
import json
import os
import sys


DATA_FILE = "tasks.json"
HISTORY_FILE = ".tasks_history.json"

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def load_data():
    """Load tasks and next_id from data file."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data["tasks"], data["next_id"]


def save_data(tasks, next_id):
    """Save tasks and next_id to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f, indent=2)


def load_history():
    """Load undo history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_undo(tasks, next_id):
    """Push current state onto undo stack."""
    history = load_history()
    history.append({"tasks": copy.deepcopy(tasks), "next_id": next_id})
    save_history(history)


def undo():
    """Undo the last mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_history(history)
    save_data(previous["tasks"], previous["next_id"])
    print("Undone")


def format_task(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        tags_str = " ".join(f"#{t}" for t in tags)
        line += " " + tags_str
    # Due date suffix
    due = task.get("due")
    if due:
        line += f' due:{due}'
    return line


def validate_date(value):
    """Validate a date string YYYY-MM-DD. Returns True if valid."""
    try:
        parts = value.split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        datetime.date(y, m, d)
        return True
    except (ValueError, OverflowError):
        return False


def cmd_add(args):
    """Add a new task."""
    title = " ".join(args.title)
    priority = args.priority if hasattr(args, "priority") and args.priority else "medium"
    if priority not in PRIORITY_ORDER:
        print(f"Invalid priority: {args.priority}", file=sys.stderr)
        sys.exit(1)

    due_date = getattr(args, "due", None)
    if due_date:
        if not validate_date(due_date):
            print(f"Invalid date: {due_date}", file=sys.stderr)
            sys.exit(1)

    tags = getattr(args, "tag", None) or []

    tasks, next_id = load_data()
    push_undo(tasks, next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due_date,
    }
    tasks.append(task)
    save_data(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    """List tasks."""
    tasks, _ = load_data()

    # Filter by tag if specified
    filter_tag = getattr(args, "tag", None)
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filter
    overdue = getattr(args, "overdue", False)
    if overdue:
        today = getattr(args, "today", None)
        if today:
            if not validate_date(today):
                print(f"Invalid date: {today}", file=sys.stderr)
                sys.exit(1)
        else:
            today = datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort by priority if requested
    sort_by = getattr(args, "sort", None)
    if sort_by == "priority":
        tasks = sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Mark a task as done."""
    task_id = args.id
    tasks, next_id = load_data()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    task["done"] = True
    save_data(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    task_id = args.id
    tasks, next_id = load_data()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks.remove(task)
    save_data(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    task_id = args.id
    new_title = " ".join(args.title)
    tasks, next_id = load_data()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    task["title"] = new_title
    save_data(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title."""
    tasks, _ = load_data()
    query = " ".join(args.text).lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Export tasks."""
    tasks, _ = load_data()
    fmt = args.format

    if fmt == "json":
        export_tasks = []
        for t in sorted(tasks, key=lambda x: x["id"]):
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in sorted(tasks, key=lambda x: x["id"]):
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")


def cmd_stats(args):
    """Print stats."""
    tasks, _ = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
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
    search_parser.add_argument("text", nargs="+")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", required=True, choices=["json", "csv"])

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

    if args.command is None:
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
        "undo": undo,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
