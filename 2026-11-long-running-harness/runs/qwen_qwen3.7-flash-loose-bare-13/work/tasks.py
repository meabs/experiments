#!/usr/bin/env python3
"""A command-line task manager."""

import argparse
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def _load():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return [], [], 0
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = data.get("tasks", [])
    undo_history = data.get("undo_history", [])
    max_id = data.get("max_id", 0)
    return tasks, undo_history, max_id


def _save(tasks, undo_history, max_id):
    """Save tasks, undo history, and max_id to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(
            {"tasks": tasks, "undo_history": undo_history, "max_id": max_id},
            f,
        )


def _task_line(task):
    """Format a task into its display line."""
    prefix = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {prefix} {task["title"]}'
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def _parse_args():
    parser = argparse.ArgumentParser(prog="tasks.py")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--tag", action="append", default=None)
    p_add.add_argument("--due", default=None)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--sort", choices=["priority", None])
    p_list.add_argument("--tag", default=None)
    p_list.add_argument("--overdue", action="store_true")
    p_list.add_argument("--today", default=None)

    # done
    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)

    # delete
    p_delete = sub.add_parser("delete")
    p_delete.add_argument("id", type=int)

    # edit
    p_edit = sub.add_parser("edit")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+")

    # search
    p_search = sub.add_parser("search")
    p_search.add_argument("text", nargs="+")

    # export
    p_export = sub.add_parser("export")
    p_export.add_argument("--format", choices=["json", "csv"], required=True)

    # stats
    sub.add_parser("stats")

    # undo
    sub.add_parser("undo")

    return parser.parse_args()


def cmd_add(args):
    tasks, undo_history, max_id = _load()

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if args.priority not in valid_priorities:
        print(f"Invalid priority: {args.priority}", file=sys.stderr)
        sys.exit(1)

    title = " ".join(args.title)
    tags = args.tag if args.tag else []

    # Validate date
    due = None
    if args.due:
        try:
            date.fromisoformat(args.due)
            due = args.due
        except ValueError:
            print(f"Invalid date: {args.due}", file=sys.stderr)
            sys.exit(1)

    new_id = max_id + 1
    new_task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": args.priority,
        "tags": tags,
        "due": due,
    }

    # Save snapshot for undo
    undo_history.append(json.dumps({"tasks": tasks, "max_id": max_id}))

    tasks.append(new_task)
    max_id = new_id
    _save(tasks, undo_history, max_id)
    print(f"Added {new_id}")


def cmd_list(args):
    tasks, _, _ = _load()

    if not tasks:
        print("No tasks")
        return

    filtered = list(tasks)

    # Filter by tag
    if args.tag:
        filtered = [t for t in filtered if args.tag in t["tags"]]

    # Filter overdue
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        filtered = [
            t for t in filtered
            if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today
        ]

    # Sort by priority
    if args.sort == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (order.get(t["priority"], 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for t in filtered:
        print(_task_line(t))


def cmd_done(args):
    tasks, undo_history, max_id = _load()

    task = None
    for t in tasks:
        if t["id"] == args.id:
            task = t
            break

    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    undo_history.append(json.dumps({"tasks": tasks, "max_id": max_id}))

    task["done"] = True
    _save(tasks, undo_history, max_id)
    print(f"Done {args.id}")


def cmd_delete(args):
    tasks, undo_history, max_id = _load()

    task = None
    for t in tasks:
        if t["id"] == args.id:
            task = t
            break

    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    undo_history.append(json.dumps({"tasks": tasks, "max_id": max_id}))

    tasks = [t for t in tasks if t["id"] != args.id]
    _save(tasks, undo_history, max_id)
    print(f"Deleted {args.id}")


def cmd_edit(args):
    tasks, undo_history, max_id = _load()

    task = None
    for t in tasks:
        if t["id"] == args.id:
            task = t
            break

    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        sys.exit(1)

    undo_history.append(json.dumps({"tasks": tasks, "max_id": max_id}))

    new_title = " ".join(args.title)
    task["title"] = new_title
    _save(tasks, undo_history, max_id)
    print(f"Edited {args.id}")


def cmd_search(args):
    tasks, _, _ = _load()

    text = " ".join(args.text).lower()
    matches = [t for t in tasks if text in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    matches.sort(key=lambda t: t["id"])
    for t in matches:
        print(_task_line(t))


def cmd_export(args):
    tasks, _, _ = _load()
    tasks.sort(key=lambda t: t["id"])

    if args.format == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output))

    elif args.format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
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
        print(buf.getvalue(), end="")


def cmd_stats(args):
    tasks, _, _ = _load()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    tasks, undo_history, max_id = _load()

    if not undo_history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = undo_history.pop()
    state = json.loads(prev_state)
    tasks = state["tasks"]
    max_id = state["max_id"]
    _save(tasks, undo_history, max_id)
    print("Undone")


def main():
    args = _parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "done":
        cmd_done(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "edit":
        cmd_edit(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "undo":
        cmd_undo(args)
    else:
        print("Unknown command", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
