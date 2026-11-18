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
UNDO_FILE = "undo.json"


def load_tasks():
    """Load tasks from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_tasks(tasks):
    """Save tasks to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def load_undo_history():
    """Load undo history from undo.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo_history(history):
    """Save undo history to undo.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_next_id(tasks):
    """Get the next available task id."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task_line(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        tag_str = " ".join(f"#{t}" for t in tags)
        line += f" {tag_str}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Add a new task."""
    priority = args.priority
    if priority is not None and priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")

    due = args.due
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    tags = args.tag or []
    title = " ".join(args.title)

    tasks = load_tasks()
    next_id = get_next_id(tasks)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }

    tasks.append(task)
    save_tasks(tasks)

    # Save undo state
    history = load_undo_history()
    history.append({
        "command": "add",
        "state": copy.deepcopy(tasks),
        "next_id": next_id,
    })
    save_undo_history(history)

    print(f"Added {next_id}")


def cmd_list(args):
    """List tasks."""
    tasks = load_tasks()

    if not tasks:
        print("No tasks")
        return

    # Filter by tag if specified
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter overdue if specified
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [
            t for t in tasks
            if not t["done"]
            and t.get("due")
            and t["due"] < today_str
        ]

    if not tasks:
        print("No tasks")
        return

    # Sort
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == args.id:
            task = t
            break

    if task is None:
        error(f"No such task: {args.id}")

    task["done"] = True
    save_tasks(tasks)

    # Save undo state
    history = load_undo_history()
    history.append({
        "command": "done",
        "state": copy.deepcopy(tasks),
        "next_id": get_next_id(tasks),
    })
    save_undo_history(history)

    print(f"Done {args.id}")


def cmd_delete(args):
    """Delete a task."""
    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == args.id:
            task = t
            break

    if task is None:
        error(f"No such task: {args.id}")

    tasks = [t for t in tasks if t["id"] != args.id]
    save_tasks(tasks)

    # Save undo state
    history = load_undo_history()
    history.append({
        "command": "delete",
        "state": copy.deepcopy(tasks),
        "next_id": get_next_id(tasks),
    })
    save_undo_history(history)

    print(f"Deleted {args.id}")


def cmd_edit(args):
    """Edit a task title."""
    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == args.id:
            task = t
            break

    if task is None:
        error(f"No such task: {args.id}")

    task["title"] = " ".join(args.title)
    save_tasks(tasks)

    # Save undo state
    history = load_undo_history()
    history.append({
        "command": "edit",
        "state": copy.deepcopy(tasks),
        "next_id": get_next_id(tasks),
    })
    save_undo_history(history)

    print(f"Edited {args.id}")


def cmd_search(args):
    """Search tasks by text."""
    tasks = load_tasks()
    query = " ".join(args.text).lower()
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    # Sort by id
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    fmt = args.format
    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(result, indent=2))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", "") or "",
            ])
        print(output.getvalue().rstrip("\n"))

    else:
        error(f"Invalid format: {fmt}")


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
    """Undo the last mutating command."""
    history = load_undo_history()

    if not history:
        error("Nothing to undo")

    last = history.pop()
    save_undo_history(history)

    # Restore state
    save_tasks(last["state"])
    print("Undone")


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", choices=["high", "medium", "low"])
    add_parser.add_argument("--tag", action="append")
    add_parser.add_argument("--due")
    add_parser.set_defaults(func=cmd_add)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", choices=["priority"])
    list_parser.add_argument("--tag")
    list_parser.add_argument("--overdue", action="store_true")
    list_parser.add_argument("--today")
    list_parser.set_defaults(func=cmd_list)

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)
    done_parser.set_defaults(func=cmd_done)

    # delete
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)
    delete_parser.set_defaults(func=cmd_delete)

    # edit
    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("--title", nargs="+")
    edit_parser.set_defaults(func=cmd_edit)

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text", nargs="+")
    search_parser.set_defaults(func=cmd_search)

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", required=True, choices=["json", "csv"])
    export_parser.set_defaults(func=cmd_export)

    # stats
    stats_parser = subparsers.add_parser("stats")
    stats_parser.set_defaults(func=cmd_stats)

    # undo
    undo_parser = subparsers.add_parser("undo")
    undo_parser.set_defaults(func=cmd_undo)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    return args


def main():
    """Main entry point."""
    args = parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        error(str(e))


if __name__ == "__main__":
    main()
