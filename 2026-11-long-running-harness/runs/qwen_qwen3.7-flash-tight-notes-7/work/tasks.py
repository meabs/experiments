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
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    """Load tasks from tasks.json, or return empty list."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        raw = data.get("tasks", [])
        # Validate and normalize tasks - ensure title is a string
        tasks = []
        for t in raw:
            if isinstance(t, dict) and "id" in t:
                if isinstance(t.get("title"), list):
                    t["title"] = " ".join(str(x) for x in t["title"])
                elif not isinstance(t.get("title"), str):
                    t["title"] = ""
                tasks.append(t)
        return tasks
    except (json.JSONDecodeError, KeyError):
        return []


def save_tasks(tasks):
    """Save tasks to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def load_history():
    """Load undo history from tasks_history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_history(history):
    """Save undo history to tasks_history.json."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(state):
    """Push current state onto history for undo."""
    history = load_history()
    snapshot = copy.deepcopy(state)
    history.append(snapshot)
    save_history(history)


def cmd_undo(args):
    """Undo the most recent mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = history.pop()
    save_history(history)
    save_tasks(previous_state["tasks"])
    print("Undone")


def get_next_id(tasks):
    """Get the next available task id."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix (only high/low shown)
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        line += f" #{tag}"
    # Due date suffix
    due = task.get("due", None)
    if due:
        line += f" due:{due}"
    return line


def validate_date(date_str):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    """Handle the 'add' command."""
    title = " ".join(args.title)
    priority = args.priority if args.priority else "medium"
    tags = args.tag if args.tag else []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate date
    if due and not validate_date(due):
        print(f"Invalid date: {due}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    new_id = get_next_id(tasks)

    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Save state before mutation for undo
    push_history({"tasks": tasks})

    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {new_id}")


def cmd_list(args):
    """Handle the 'list' command."""
    tasks = load_tasks()

    # Filter by tag
    if args.tag:
        tag_filter = args.tag
        tasks = [t for t in tasks if any(tag in t.get("tags", []) for tag in tag_filter)]

    # Overdue filter
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        if not validate_date(today_str):
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        cutoff = datetime.strptime(today_str, "%Y-%m-%d").date()
        tasks = [
            t for t in tasks
            if not t["done"]
            and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < cutoff
        ]

    # Sort by priority
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    tasks = load_tasks()
    task_id = args.id

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history({"tasks": tasks})
    task["done"] = True
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    tasks = load_tasks()
    task_id = args.id

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history({"tasks": tasks})
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    tasks = load_tasks()
    task_id = args.id

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history({"tasks": tasks})
    new_title = " ".join(args.title)
    task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    tasks = load_tasks()
    text = args.text.lower()

    matches = [t for t in tasks if text in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    # Sort by id
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    tasks = load_tasks()
    fmt = args.format

    if fmt == "json":
        output = []
        for t in sorted(tasks, key=lambda x: x["id"]):
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(output, indent=2))

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
        print(output.getvalue().rstrip("\n"))


def cmd_stats(args):
    """Handle the 'stats' command."""
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
    list_parser.add_argument("--sort", default=None)
    list_parser.add_argument("--tag", action="append", default=None)
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
    export_parser.add_argument("--format", choices=["json", "csv"], required=True)

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
