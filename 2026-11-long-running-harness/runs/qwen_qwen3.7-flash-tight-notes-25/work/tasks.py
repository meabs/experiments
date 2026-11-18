#!/usr/bin/env python3
"""A command-line task manager."""

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
    """Load tasks and undo history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def push_undo(data):
    """Push a snapshot of current state onto the undo history."""
    data["undo_history"].append({
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    })
    # Keep history manageable - cap at 100 entries
    if len(data["undo_history"]) > 100:
        data["undo_history"] = data["undo_history"][-100:]


def format_task_line(task):
    """Format a task for display in list/search."""
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
        line += " " + " ".join(f"#{tag}" for tag in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_args(argv):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=[])
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", default=None)
    list_parser.add_argument("--tag", default=None)
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
    search_parser.add_argument("text")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", dest="fmt", required=True)

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    return parser.parse_args(argv)


def main():
    try:
        args = parse_args(sys.argv[1:])
    except SystemExit as e:
        raise SystemExit(1)

    data = load_data()

    if args.command == "add":
        title = " ".join(args.title)
        priority = args.priority
        if priority not in ("high", "medium", "low"):
            print(f"Invalid priority: {priority}", file=sys.stderr)
            sys.exit(1)
        due = None
        if args.due is not None:
            try:
                date.fromisoformat(args.due)
                due = args.due
            except ValueError:
                print(f"Invalid date: {args.due}", file=sys.stderr)
                sys.exit(1)
        tags = args.tag if args.tag else []

        push_undo(data)
        task = {
            "id": data["next_id"],
            "title": title,
            "done": False,
            "priority": priority,
            "tags": tags,
            "due": due,
        }
        data["tasks"].append(task)
        data["next_id"] += 1
        save_data(data)
        print(f"Added {task['id']}")

    elif args.command == "list":
        tasks = data["tasks"]
        if not tasks:
            print("No tasks")
            return

        # Filter by tag
        if args.tag:
            tasks = [t for t in tasks if args.tag in t.get("tags", [])]

        # Filter by overdue
        if args.overdue:
            today_str = args.today
            if today_str is None:
                today_str = date.today().isoformat()
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
            tasks = [
                t for t in tasks
                if not t["done"] and t.get("due") is not None
                and date.fromisoformat(t["due"]) < today
            ]

        if not tasks:
            print("No tasks")
            return

        # Sort
        if args.sort == "priority":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            tasks = sorted(tasks, key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 1),
                t["id"]
            ))

        for task in tasks:
            print(format_task_line(task))

    elif args.command == "done":
        task_id = args.id
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"No such task: {task_id}", file=sys.stderr)
            sys.exit(1)
        push_undo(data)
        task["done"] = True
        save_data(data)
        print(f"Done {task_id}")

    elif args.command == "delete":
        task_id = args.id
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"No such task: {task_id}", file=sys.stderr)
            sys.exit(1)
        push_undo(data)
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        save_data(data)
        print(f"Deleted {task_id}")

    elif args.command == "edit":
        task_id = args.id
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"No such task: {task_id}", file=sys.stderr)
            sys.exit(1)
        new_title = " ".join(args.title)
        push_undo(data)
        task["title"] = new_title
        save_data(data)
        print(f"Edited {task_id}")

    elif args.command == "search":
        text = args.text.lower()
        matches = [t for t in data["tasks"] if text in t["title"].lower()]
        # Sort by id
        matches.sort(key=lambda t: t["id"])
        if not matches:
            print("No matches")
            return
        for task in matches:
            print(format_task_line(task))

    elif args.command == "export":
        fmt = args.fmt
        tasks = sorted(data["tasks"], key=lambda t: t["id"])
        if fmt == "json":
            output = []
            for task in tasks:
                output.append({
                    "id": task["id"],
                    "title": task["title"],
                    "done": task["done"],
                    "priority": task.get("priority", "medium"),
                    "tags": task.get("tags", []),
                    "due": task.get("due"),
                })
            print(json.dumps(output))
        elif fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "title", "done", "priority", "tags", "due"])
            for task in tasks:
                writer.writerow([
                    task["id"],
                    task["title"],
                    str(task["done"]).lower(),
                    task.get("priority", "medium"),
                    ";".join(task.get("tags", [])),
                    task.get("due", ""),
                ])
            print(output.getvalue(), end="")
        else:
            print(f"Invalid format: {fmt}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "stats":
        open_count = sum(1 for t in data["tasks"] if not t["done"])
        done_count = sum(1 for t in data["tasks"] if t["done"])
        total = len(data["tasks"])
        print(f"open: {open_count}")
        print(f"done: {done_count}")
        print(f"total: {total}")

    elif args.command == "undo":
        if not data["undo_history"]:
            print("Nothing to undo", file=sys.stderr)
            sys.exit(1)
        snapshot = data["undo_history"].pop()
        data["tasks"] = snapshot["tasks"]
        data["next_id"] = snapshot["next_id"]
        save_data(data)
        print("Undone")

    else:
        print("Unknown command", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
