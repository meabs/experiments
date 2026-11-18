#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    """Load tasks from data file, or return empty list if not found."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def load_undo_history():
    """Load undo history from file, or return empty list if not found."""
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo_history(history):
    """Save undo history to file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def next_id(tasks):
    """Compute the next available id (max id + 1, or 1 if no tasks)."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Add a new task."""
    title = " ".join(args.title)
    priority = args.priority
    tags = args.tag or []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        error(f"Invalid priority: {priority}")

    # Validate due date
    if due is not None:
        try:
            date.fromisoformat(due)
        except ValueError:
            error(f"Invalid date: {due}")

    tasks = load_tasks()
    task_id = next_id(tasks)
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)

    # Record undo state
    history = load_undo_history()
    history.append({"type": "add", "task": task})
    save_undo_history(history)

    print(f"Added {task_id}")


def cmd_list(args):
    """List tasks with optional filtering and sorting."""
    tasks = load_tasks()

    # Filter by tag
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter overdue
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today
        ]

    # Sort
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    elif args.sort is not None:
        error(f"Unknown sort option: {args.sort}")
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    task_id = args.id
    tasks = load_tasks()
    found = False
    prev_done = None
    for task in tasks:
        if task["id"] == task_id:
            prev_done = task["done"]
            task["done"] = True
            found = True
            break
    if not found:
        error(f"No such task: {task_id}")
    save_tasks(tasks)

    # Record undo state
    history = load_undo_history()
    history.append({
        "type": "done",
        "id": task_id,
        "prev_done": prev_done,
    })
    save_undo_history(history)

    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    task_id = args.id
    tasks = load_tasks()
    found = False
    deleted_task = None
    new_tasks = []
    for task in tasks:
        if task["id"] == task_id:
            found = True
            deleted_task = task
        else:
            new_tasks.append(task)
    if not found:
        error(f"No such task: {task_id}")
    save_tasks(new_tasks)

    # Record undo state
    history = load_undo_history()
    history.append({
        "type": "delete",
        "task": deleted_task,
    })
    save_undo_history(history)

    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    task_id = args.id
    new_title = " ".join(args.title)
    tasks = load_tasks()
    found = False
    old_title = None
    for task in tasks:
        if task["id"] == task_id:
            old_title = task["title"]
            task["title"] = new_title
            found = True
            break
    if not found:
        error(f"No such task: {task_id}")
    save_tasks(tasks)

    # Record undo state
    history = load_undo_history()
    history.append({
        "type": "edit",
        "id": task_id,
        "old_title": old_title,
    })
    save_undo_history(history)

    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by title (case-insensitive)."""
    tasks = load_tasks()
    query = args.text.lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


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
            writer.writerow([
                task["id"],
                task["title"],
                "true" if task["done"] else "false",
                task.get("priority", "medium"),
                ";".join(task.get("tags", [])),
                task.get("due") or "",
            ])
        print(output.getvalue(), end="")

    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Show task statistics."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the most recent mutating command."""
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    action = history.pop()
    save_undo_history(history)

    tasks = load_tasks()

    if action["type"] == "add":
        # Remove the added task
        task_id = action["task"]["id"]
        tasks = [t for t in tasks if t["id"] != task_id]
        save_tasks(tasks)

    elif action["type"] == "done":
        # Restore the task to its previous state
        task_id = action["id"]
        for task in tasks:
            if task["id"] == task_id:
                task["done"] = action["prev_done"]
                break
        save_tasks(tasks)

    elif action["type"] == "delete":
        # Re-add the deleted task
        deleted_task = action["task"]
        tasks.append(deleted_task)
        save_tasks(tasks)

    elif action["type"] == "edit":
        # Restore the old title
        task_id = action["id"]
        for task in tasks:
            if task["id"] == task_id:
                task["title"] = action["old_title"]
                break
        save_tasks(tasks)

    print("Undone")


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=None)
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", choices=["priority"])
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
    edit_parser.add_argument("--title", nargs="+")

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

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
