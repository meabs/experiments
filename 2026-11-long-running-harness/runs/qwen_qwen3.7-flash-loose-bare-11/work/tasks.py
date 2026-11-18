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
UNDO_FILE = "undo_history.json"


def load_tasks():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_tasks(tasks):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo_history():
    """Load undo history from file."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo_history(history):
    """Save undo history to file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def get_next_id(tasks):
    """Get the next available task id."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        tag_suffix = " ".join(f"#{t}" for t in tags)
        line += " " + tag_suffix
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def save_undo_snapshot(action_name):
    """Save a snapshot of current tasks for undo."""
    history = load_undo_history()
    history.append({
        "action": action_name,
        "state_before": copy.deepcopy(load_tasks()),
    })
    save_undo_history(history)


def cmd_add(args):
    """Handle the 'add' command."""
    title_parts = args.title
    priority = getattr(args, "priority", None) or "medium"
    tags = getattr(args, "tag", None) or []
    due = getattr(args, "due", None)

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        error(f"Invalid priority: {priority}")

    # Validate date
    if due:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    tasks = load_tasks()
    new_id = get_next_id(tasks)

    task = {
        "id": new_id,
        "title": " ".join(title_parts),
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)

    # Save undo state before mutation
    save_undo_snapshot("add")

    save_tasks(tasks)
    print(f"Added {new_id}")


def cmd_list(args):
    """Handle the 'list' command."""
    tasks = load_tasks()

    # Filter by tag if specified
    filter_tag = getattr(args, "tag", None)
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue if specified
    overdue_filter = getattr(args, "overdue", None)
    if overdue_filter:
        today_str = getattr(args, "today", None) or date.today().isoformat()
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            today_date = date.today()
        overdue_tasks = []
        for t in tasks:
            if t.get("due"):
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if t["done"]:
                        continue
                    if due_date < today_date:
                        overdue_tasks.append(t)
                except ValueError:
                    pass
        tasks = overdue_tasks

    # Sort by priority if requested
    sort_by = getattr(args, "sort", None)
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    tasks = load_tasks()
    task_id = args.id

    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    # Save undo state before mutation
    save_undo_snapshot("done")

    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    tasks = load_tasks()
    task_id = args.id

    found = False
    new_tasks = []
    for task in tasks:
        if task["id"] == task_id:
            found = True
        else:
            new_tasks.append(task)

    if not found:
        error(f"No such task: {task_id}")

    # Save undo state before mutation
    save_undo_snapshot("delete")

    save_tasks(new_tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    tasks = load_tasks()
    task_id = args.id

    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = " ".join(args.title)
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    # Save undo state before mutation
    save_undo_snapshot("edit")

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

    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    fmt = args.format
    tasks = load_tasks()

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))

    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                tags_str,
                due_str,
            ])
        print(buf.getvalue(), end="")


def cmd_stats(args):
    """Handle the 'stats' command."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    state = history.pop()["state_before"]
    save_undo_history(history)
    save_tasks(state)
    print("Undone")


def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(description="Command-line task manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", nargs="+", help="Task title")
    add_parser.add_argument("--priority", default=None)
    add_parser.add_argument("--tag", action="append", default=None)
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--tag", default=None)
    list_parser.add_argument("--overdue", action="store_true", default=False)
    list_parser.add_argument("--today", default=None)
    list_parser.add_argument("--sort", default=None)

    # done
    done_parser = subparsers.add_parser("done", help="Mark a task as done")
    done_parser.add_argument("id", type=int, help="Task ID")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int, help="Task ID")

    # edit
    edit_parser = subparsers.add_parser("edit", help="Edit a task")
    edit_parser.add_argument("id", type=int, help="Task ID")
    edit_parser.add_argument("--title", nargs="+", required=True, help="New title")

    # search
    search_parser = subparsers.add_parser("search", help="Search tasks")
    search_parser.add_argument("text", help="Search text")

    # export
    export_parser = subparsers.add_parser("export", help="Export tasks")
    export_parser.add_argument("--format", choices=["json", "csv"], required=True)

    # stats
    subparsers.add_parser("stats", help="Show task statistics")

    # undo
    subparsers.add_parser("undo", help="Undo last action")

    return parser


def main():
    """Main entry point."""
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
        error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
