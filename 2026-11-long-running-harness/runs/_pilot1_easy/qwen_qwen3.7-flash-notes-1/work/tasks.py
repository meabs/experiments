#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import argparse
import copy
import csv
import io
import json
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from tasks.json."""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"tasks": [], "undo_history": []}
    except json.JSONDecodeError:
        return {"tasks": [], "undo_history": []}
    return data


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def next_id(tasks):
    """Return the next available task id."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]
    # Priority suffix
    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        parts.append(" ".join(f"#{t}" for t in tags))
    # Due date suffix
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def add_task(args):
    """Handle 'add' command."""
    data = load_data()
    title = " ".join(args.title)
    priority = args.priority
    tags = args.tag if args.tag else []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    # Validate date if provided
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    task = {
        "id": next_id(data["tasks"]),
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Save state for undo
    data["undo_history"].append(copy.deepcopy(data["tasks"]))

    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task['id']}")


def list_tasks(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = data["tasks"]

    # Filter by tag if specified
    if hasattr(args, "filter_tag") and args.filter_tag:
        tag_filter = args.filter_tag
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue if specified
    if hasattr(args, "overdue") and args.overdue:
        today_str = getattr(args, "today", None)
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today
        ]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if hasattr(args, "sort") and args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for t in tasks:
        print(task_line(t))


def done_task(args):
    """Handle 'done' command."""
    data = load_data()
    task_id = args.id

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    data["undo_history"].append(copy.deepcopy(data["tasks"]))

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def delete_task(args):
    """Handle 'delete' command."""
    data = load_data()
    task_id = args.id

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    data["undo_history"].append(copy.deepcopy(data["tasks"]))

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def edit_task(args):
    """Handle 'edit' command."""
    data = load_data()
    task_id = args.id

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    data["undo_history"].append(copy.deepcopy(data["tasks"]))

    new_title = " ".join(args.title)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def search_tasks(args):
    """Handle 'search' command."""
    data = load_data()
    query = " ".join(args.text).lower()

    matches = [t for t in data["tasks"] if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def export_tasks(args):
    """Handle 'export' command."""
    data = load_data()
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due") or "",
            ])
        print(output.getvalue(), end="")


def stats_command(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def undo_command(args):
    """Handle 'undo' command."""
    data = load_data()
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    # Pop the last saved state
    prev_tasks = data["undo_history"].pop()
    data["tasks"] = prev_tasks
    save_data(data)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+", help="Task title")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=None)
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", default=None)
    list_parser.add_argument("--tag", dest="filter_tag", default=None)
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
    search_parser.add_argument("text", nargs="+", help="Search text")

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

    if args.command == "add":
        add_task(args)
    elif args.command == "list":
        list_tasks(args)
    elif args.command == "done":
        done_task(args)
    elif args.command == "delete":
        delete_task(args)
    elif args.command == "edit":
        edit_task(args)
    elif args.command == "search":
        search_tasks(args)
    elif args.command == "export":
        export_tasks(args)
    elif args.command == "stats":
        stats_command(args)
    elif args.command == "undo":
        undo_command(args)


if __name__ == "__main__":
    main()
