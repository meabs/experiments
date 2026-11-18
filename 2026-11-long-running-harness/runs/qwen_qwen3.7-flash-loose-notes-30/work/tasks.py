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
    """Load tasks from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    """Save tasks to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    """Load undo history from JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to JSON file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(tasks_data):
    """Push current state onto undo history."""
    history = load_history()
    history.append(json.dumps(tasks_data))
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def undo(args=None):
    """Revert the most recent mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = json.loads(history.pop())
    save_history(history)
    save_tasks(previous_state)
    print("Undone")


def format_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_date(date_str):
    """Validate and parse a YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    """Add a new task."""
    title = " ".join(args.title)
    priority = args.priority if args.priority is not None else "medium"
    tags = args.tag or []
    due = args.due or None

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate date
    if due is not None:
        if not parse_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    data = load_tasks()
    push_history(data)

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
    save_tasks(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """List tasks."""
    data = load_tasks()
    tasks = list(data["tasks"])

    if not tasks:
        print("No tasks")
        return

    # Filter by tag if specified
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter overdue if specified
    if args.overdue:
        today_str = args.today
        if today_str:
            if not parse_date(today_str):
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
        else:
            today_str = date.today().isoformat()
        today = datetime.strptime(today_str, "%Y-%m-%d").date()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    task_id = args.id
    data = load_tasks()
    push_history(data)

    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(data)
            print(f"Done {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Delete a task."""
    task_id = args.id
    data = load_tasks()
    push_history(data)

    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"].pop(i)
            save_tasks(data)
            print(f"Deleted {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    """Edit a task's title."""
    task_id = args.id
    new_title = " ".join(args.title)
    data = load_tasks()
    push_history(data)

    for task in data["tasks"]:
        if task["id"] == task_id:
            task["title"] = new_title
            save_tasks(data)
            print(f"Edited {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Search tasks by title."""
    data = load_tasks()
    text = args.text.lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    # Sort by id order
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    data = load_tasks()
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due", None),
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
                task.get("priority", "medium"),
                ";".join(task.get("tags", [])),
                task.get("due", ""),
            ])
        print(output.getvalue(), end="")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Print task statistics."""
    data = load_tasks()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
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
    add_parser.add_argument("--tag", action="append", default=[])
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", choices=["priority"], default=None)
    list_parser.add_argument("--tag", default=None)
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
    export_parser.add_argument("--format", choices=["json", "csv"], required=True)

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
