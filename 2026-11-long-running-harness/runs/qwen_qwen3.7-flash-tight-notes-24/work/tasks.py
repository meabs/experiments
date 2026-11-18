#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
import copy
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Persist tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def snapshot(data):
    """Save current state into undo history."""
    data["history"].append({
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    })


def restore_state(data):
    """Restore the last state from undo history."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)


def format_task_line(task_id, task):
    """Format a single task line for display."""
    status = "x" if task["done"] else " "
    line = f"{task_id} [{status}] {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def do_add(args, data):
    """Handle the 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    snapshot(data)

    task_id = str(data["next_id"])
    data["next_id"] += 1
    data["tasks"][task_id] = {
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_data(data)
    print(f"Added {task_id}")


def do_list(args, data):
    """Handle the 'list' command."""
    sort_mode = None
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            if sort_mode != "priority":
                print(f"Unknown sort mode: {sort_mode}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("Missing value for --today", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    today = date.fromisoformat(today_str) if today_str else date.today()

    tasks = list(data["tasks"].items())

    if tag_filter:
        tasks = [(tid, t) for tid, t in tasks if tag_filter in t["tags"]]

    if overdue:
        filtered = []
        for tid, t in tasks:
            if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today:
                filtered.append((tid, t))
        tasks = filtered

    if sort_mode == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda x: (prio_order.get(x[1]["priority"], 1), int(x[0])))

    if not tasks:
        print("No tasks")
        return

    for tid, t in tasks:
        print(format_task_line(tid, t))


def do_done(args, data):
    """Handle the 'done' command."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = str(int(args[0]))
    except ValueError:
        print(f"Invalid id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in data["tasks"]:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    snapshot(data)
    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {args[0]}")


def do_delete(args, data):
    """Handle the 'delete' command."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = str(int(args[0]))
    except ValueError:
        print(f"Invalid id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in data["tasks"]:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    snapshot(data)
    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {args[0]}")


def do_edit(args, data):
    """Handle the 'edit' command."""
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = str(int(args[0]))
    except ValueError:
        print(f"Invalid id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in data["tasks"]:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1  # skip task id
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                print("Missing value for --title", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    snapshot(data)
    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def do_search(args, data):
    """Handle the 'search' command."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    results = []
    for tid in sorted(data["tasks"].keys(), key=int):
        task = data["tasks"][tid]
        if query in task["title"].lower():
            results.append((tid, task))

    if not results:
        print("No matches")
        return

    for tid, t in results:
        print(format_task_line(tid, t))


def do_export(args, data):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing value for --format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Unknown format: {fmt}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks_sorted = sorted(data["tasks"].items(), key=lambda x: int(x[0]))

    if fmt == "json":
        result = []
        for tid, t in tasks_sorted:
            result.append({
                "id": int(tid),
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for tid, t in tasks_sorted:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{tid},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def do_stats(args, data):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in data["tasks"].values() if not t["done"])
    done_count = sum(1 for t in data["tasks"].values() if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(args, data):
    """Handle the 'undo' command."""
    restore_state(data)
    print("Undone")


COMMANDS = {
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
