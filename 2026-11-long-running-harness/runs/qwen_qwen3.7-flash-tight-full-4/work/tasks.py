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


def load_data():
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
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


def cmd_add(args):
    """Add a new task."""
    data = load_data()
    title = " ".join(args.title)
    priority = args.priority if args.priority else "medium"
    tags = args.tag if args.tag else []
    due = args.due

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        error(f"Invalid priority: {priority}")

    # Validate due date
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    # Record undo state before mutation
    old_state = json.dumps({
        "tasks": data["tasks"][:-1],
        "next_id": data["next_id"],
    })
    data["history"].append(old_state)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """List tasks, optionally filtered or sorted."""
    data = load_data()
    tasks = list(data["tasks"])

    # Filter by tag
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter overdue
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and t["due"] < today_str
        ]

    # Sort by priority
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        if args.overdue or args.tag:
            pass  # just print nothing for filtered views
        else:
            print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    tid = args.id
    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        error(f"No such task: {tid}")
    old_state = json.dumps({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    data["history"].append(old_state)
    task["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    tid = args.id
    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        error(f"No such task: {tid}")
    old_state = json.dumps({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    data["history"].append(old_state)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args):
    """Edit a task's title."""
    data = load_data()
    tid = args.id
    task = next((t for t in data["tasks"] if t["id"] == tid), None)
    if task is None:
        error(f"No such task: {tid}")
    old_state = json.dumps({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    data["history"].append(old_state)
    task["title"] = " ".join(args.title)
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args):
    """Search tasks by title substring."""
    data = load_data()
    text = args.text.lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    data = load_data()
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
        print(json.dumps(export_tasks, indent=2))
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
                t.get("due") or "",
            ])
        print(buf.getvalue(), end="")


def cmd_stats(args):
    """Show task statistics."""
    data = load_data()
    tasks = data["tasks"]
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")
    old_state = json.loads(data["history"].pop())
    data["tasks"] = old_state["tasks"]
    data["next_id"] = old_state["next_id"]
    save_data(data)
    print("Undone")


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
    list_parser.add_argument("--sort", default=None)
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
    search_parser.add_argument("text")

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
