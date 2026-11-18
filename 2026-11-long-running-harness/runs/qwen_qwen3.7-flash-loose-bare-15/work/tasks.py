#!/usr/bin/env python3
"""Command-line task manager."""

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
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, KeyError):
        return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    """Persist tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a single task for display."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f'{task["id"]} {status} {task["title"]}']
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium has no suffix
    # Tags suffix
    if task.get("tags"):
        parts.extend([f"#{t}" for t in task["tags"]])
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args):
    """Add a new task."""
    priority = args.priority
    if priority is not None:
        valid_priorities = ("high", "medium", "low")
        if priority not in valid_priorities:
            print(f"Invalid priority: {priority}", file=sys.stderr)
            sys.exit(1)

    tags = args.tag if args.tag else []
    due = args.due

    if due is not None:
        try:
            date.fromisoformat(due)
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    title = " ".join(args.title)

    data = load_data()
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    # Save state for undo (deep copy of tasks list and next_id before mutation)
    data["history"].append(copy.deepcopy({
        "tasks": data["tasks"][:-1],  # tasks before this add
        "next_id": data["next_id"] - 1,
    }))

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """List tasks with optional filtering and sorting."""
    data = load_data()
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return

    result = list(tasks)

    # Filter by tag
    if args.tag:
        result = [t for t in result if args.tag in t.get("tags", [])]

    # Filter overdue
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        today_date = date.fromisoformat(today_str)
        result = [
            t for t in result
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today_date
        ]

    # Sort by priority
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not result:
        print("No tasks")
        return

    for task in result:
        print(task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    task = _find_task(data, args.id)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    prev_tasks = copy.deepcopy(data["tasks"])
    task["done"] = True

    data["history"].append({
        "tasks": prev_tasks,
        "next_id": data["next_id"],
    })

    save_data(data)
    print(f"Done {task['id']}")


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    idx = _find_task_index(data, args.id)
    if idx is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    prev_tasks = copy.deepcopy(data["tasks"])
    del data["tasks"][idx]

    data["history"].append({
        "tasks": prev_tasks,
        "next_id": data["next_id"],
    })

    save_data(data)
    print(f"Deleted {args.id}")


def cmd_edit(args):
    """Edit a task's title."""
    data = load_data()
    task = _find_task(data, args.id)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    prev_tasks = copy.deepcopy(data["tasks"])
    task["title"] = " ".join(args.title)

    data["history"].append({
        "tasks": prev_tasks,
        "next_id": data["next_id"],
    })

    save_data(data)
    print(f"Edited {task['id']}")


def cmd_search(args):
    """Search tasks by title (case-insensitive)."""
    data = load_data()
    query = args.text.lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    # Sort by id
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    data = load_data()
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_list = []
        for t in tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_list, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(output.getvalue().rstrip("\r\n"))


def cmd_stats(args):
    """Print task statistics."""
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]

    save_data(data)
    print("Undone")


def _find_task(data, task_id):
    """Find a task by id. Returns the task dict or None."""
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def _find_task_index(data, task_id):
    """Find the index of a task by id. Returns the index or None."""
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            return i
    return None


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority", default=None)
    p_add.add_argument("--tag", action="append", default=None)
    p_add.add_argument("--due", default=None)

    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", default=None)
    p_list.add_argument("--tag", default=None)
    p_list.add_argument("--overdue", action="store_true", default=False)
    p_list.add_argument("--today", default=None)

    # done
    p_done = subparsers.add_parser("done")
    p_done.add_argument("id", type=int)

    # delete
    p_delete = subparsers.add_parser("delete")
    p_delete.add_argument("id", type=int)

    # edit
    p_edit = subparsers.add_parser("edit")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+", required=True)

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("text")

    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("--format", required=True, choices=["json", "csv"])

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
        "undo": cmd_undo,
    }

    cmd = commands[args.command]
    cmd(args)


if __name__ == "__main__":
    main()
