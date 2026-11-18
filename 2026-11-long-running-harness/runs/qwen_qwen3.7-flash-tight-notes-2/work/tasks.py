#!/usr/bin/env python3
"""A command-line task manager using Python 3 standard library only."""

import argparse
import copy
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a single task for display."""
    done_marker = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_marker} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def do_add(data, args):
    """Handle the add command."""
    if not args.title:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    # Parse priority
    priority = args.priority if args.priority else "medium"
    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")

    # Parse tags
    tags = args.tag if args.tag else []

    # Parse due date
    due = None
    if args.due:
        try:
            date.fromisoformat(args.due)
            due = args.due
        except ValueError:
            error(f"Invalid date: {args.due}")

    # Save state BEFORE mutation for undo
    data["history"].append(copy.deepcopy(data))

    task = {
        "id": data["next_id"],
        "title": " ".join(args.title),
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def do_list(data, args):
    """Handle the list command."""
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return

    # Filter by tag
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Overdue filter
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    # Sort
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    for task in tasks:
        print(task_line(task))


def do_done(data, args):
    """Handle the done command."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation for undo
    data["history"].append(copy.deepcopy(data))

    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def do_delete(data, args):
    """Handle the delete command."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation for undo
    data["history"].append(copy.deepcopy(data))

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(data, args):
    """Handle the edit command."""
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")

    # Save state BEFORE mutation for undo
    data["history"].append(copy.deepcopy(data))

    task["title"] = " ".join(args.title)
    save_data(data)
    print(f"Edited {task_id}")


def do_search(data, args):
    """Handle the search command."""
    text = args.text.lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in sorted(matches, key=lambda t: t["id"]):
        print(task_line(task))


def do_export(data, args):
    """Handle the export command."""
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
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
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")
    else:
        error(f"Unknown format: {fmt}")


def do_stats(data, args):
    """Handle the stats command."""
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(data, args):
    """Handle the undo command."""
    if not data["history"]:
        error("Nothing to undo")
    previous_state = data["history"].pop()
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
    save_data(data)
    print("Undone")


def parse_args(argv=None):
    """Parse command-line arguments."""
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

    return parser.parse_args(argv)


def main():
    args = parse_args()
    if not args.command:
        error("Usage: python3 tasks.py <command> [args]")

    data = load_data()

    commands = {
        "add": do_add,
        "list": do_list,
        "done": do_done,
        "delete": do_delete,
        "edit": do_edit,
        "search": do_search,
        "export": do_export,
        "stats": do_stats,
        "undo": do_undo,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(data, args)
    else:
        error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
