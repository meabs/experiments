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


TASKS_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    """Load tasks from tasks.json."""
    if not os.path.exists(TASKS_FILE):
        return [], 1
    try:
        with open(TASKS_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        next_id = data.get("next_id", 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    """Save tasks to tasks.json."""
    data = {"tasks": tasks, "next_id": next_id}
    with open(TASKS_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    """Load undo history."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo(history):
    """Save undo history."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def record_undo(tasks, next_id):
    """Record current state for undo."""
    history = load_undo()
    history.append({"tasks": copy.deepcopy(tasks), "next_id": next_id})
    save_undo(history)


def undo_action():
    """Undo the most recent mutating command."""
    history = load_undo()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_tasks(previous["tasks"], previous["next_id"])
    save_undo(history)
    print("Undone")


def format_task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
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
    if task.get("due"):
        line += f' due:{task["due"]}'
    return line


def parse_date(date_str):
    """Validate a YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    """Handle add command."""
    title = args.title
    priority = getattr(args, 'priority', 'medium') or 'medium'
    tags = getattr(args, 'tag', None) or []
    due = getattr(args, 'due', None)

    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    if due is not None:
        if not parse_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    tasks, next_id = load_tasks()
    new_task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(new_task)
    save_tasks(tasks, next_id + 1)
    record_undo(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    """Handle list command."""
    tasks, next_id = load_tasks()

    # Filter by tag
    if hasattr(args, 'tag') and args.tag:
        tag_filter = args.tag
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter
    if hasattr(args, 'overdue') and args.overdue:
        today_str = getattr(args, 'today', None) or date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]

    # Sort by priority if requested
    if hasattr(args, 'sort') and args.sort == 'priority':
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Handle done command."""
    tasks, next_id = load_tasks()
    task_id = args.id

    found = None
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            found = i
            break

    if found is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    tasks[found]["done"] = True
    save_tasks(tasks, next_id)
    record_undo(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle delete command."""
    tasks, next_id = load_tasks()
    task_id = args.id

    found = None
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            found = i
            break

    if found is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    del tasks[found]
    save_tasks(tasks, next_id)
    record_undo(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle edit command."""
    tasks, next_id = load_tasks()
    task_id = args.id

    found = None
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            found = i
            break

    if found is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    new_title = args.title
    tasks[found]["title"] = new_title
    save_tasks(tasks, next_id)
    record_undo(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle search command."""
    tasks, next_id = load_tasks()
    query = args.text.lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle export command."""
    tasks, next_id = load_tasks()
    tasks = sorted(tasks, key=lambda t: t["id"])
    fmt = args.format

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(output))
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
    """Handle stats command."""
    tasks, next_id = load_tasks()
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def main():
    parser = argparse.ArgumentParser(description="Task Manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
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

    if args.command == "add":
        title = " ".join(args.title)
        cmd_add(type('Args', (), {'title': title, 'priority': args.priority, 'tag': args.tag, 'due': args.due})())
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "done":
        cmd_done(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "edit":
        title = " ".join(args.title)
        cmd_edit(type('Args', (), {'id': args.id, 'title': title})())
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "undo":
        undo_action()


if __name__ == "__main__":
    main()
