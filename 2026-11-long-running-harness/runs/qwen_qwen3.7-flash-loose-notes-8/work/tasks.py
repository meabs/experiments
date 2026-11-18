#!/usr/bin/env python3
"""A command-line task manager."""

import argparse
import copy
import csv
import io
import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return (
            data.get("tasks", []),
            data.get("undo_history", []),
            data.get("next_id", 1),
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return [], [], 1


def save_data(tasks, undo_history, next_id=None):
    """Save tasks and undo history to the data file."""
    data = {
        "tasks": tasks,
        "undo_history": undo_history,
        "next_id": next_id if next_id is not None else _compute_next_id(tasks),
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def _compute_next_id(tasks):
    """Compute the next available id from tasks."""
    if tasks:
        return max(t["id"] for t in tasks) + 1
    return 1


def format_task(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    for tag in task["tags"]:
        line += f" #{tag}"
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle the 'add' command."""
    tasks, undo_history, next_id = load_data()
    priority = args.priority
    title_parts = args.title

    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tags = args.tag if args.tag else []
    due = args.due

    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    # Snapshot the current state before mutation
    undo_history.append(copy.deepcopy(tasks))

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    new_next_id = next_id + 1

    save_data(tasks, undo_history, new_next_id)

    print(f"Added {next_id}")


def cmd_list(args):
    """Handle the 'list' command."""
    tasks, _, _ = load_data()

    if not tasks:
        print("No tasks")
        return

    filtered = tasks[:]

    # Filter by tag
    if args.tag:
        filtered = [t for t in filtered if args.tag in t["tags"]]

    # Overdue filter: open tasks whose due date < today
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        today = date.fromisoformat(today_str)
        filtered = [
            t for t in filtered
            if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today
        ]

    # Sort
    if args.sort == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (prio_order.get(t["priority"], 1), t["id"]))
    elif args.sort == "due":
        filtered.sort(key=lambda t: (t["due"] or "9999-12-31", t["id"]))

    for task in filtered:
        print(format_task(task))


def cmd_done(args):
    """Handle the 'done' command."""
    tasks, undo_history, next_id = load_data()
    task_id = args.id

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Snapshot before mutation
    undo_history.append(copy.deepcopy(tasks))

    task["done"] = True

    save_data(tasks, undo_history, next_id)

    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    tasks, undo_history, next_id = load_data()
    task_id = args.id

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Snapshot before mutation
    undo_history.append(copy.deepcopy(tasks))

    tasks.remove(task)

    save_data(tasks, undo_history, next_id)

    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    tasks, undo_history, next_id = load_data()
    task_id = args.id

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Snapshot before mutation
    undo_history.append(copy.deepcopy(tasks))

    new_title = " ".join(args.title)
    task["title"] = new_title

    save_data(tasks, undo_history, next_id)

    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    tasks, _, _ = load_data()
    query = " ".join(args.text).lower()

    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in sorted(matches, key=lambda t: t["id"]):
        print(format_task(task))


def cmd_export(args):
    """Handle the 'export' command."""
    tasks, _, _ = load_data()

    if args.format == "json":
        output = []
        for t in sorted(tasks, key=lambda x: x["id"]):
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output, indent=2))
    elif args.format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in sorted(tasks, key=lambda x: x["id"]):
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] or "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args):
    """Handle the 'stats' command."""
    tasks, _, _ = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the 'undo' command."""
    tasks, undo_history, next_id = load_data()

    if not undo_history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    previous_state = undo_history.pop()
    save_data(previous_state, undo_history, next_id)

    print("Undone")


def main():
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
    list_parser.add_argument("--sort", choices=["priority", "due"])
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
    edit_parser.add_argument("--title", nargs="+", required=True)

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text", nargs="+")

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

    commands[args.command](args)


if __name__ == "__main__":
    main()
