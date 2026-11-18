#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def err(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def load_tasks():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", [])


def save_tasks(tasks):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f)


def load_history():
    """Load undo history from history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history to history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def next_id(tasks):
    """Return the next id to assign (1 + max of existing ids, or 1)."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def _find_task(tid, tasks):
    """Find a task by id. Returns the task dict or None."""
    for t in tasks:
        if t["id"] == tid:
            return t
    return None


def validate_date(value):
    """Validate a YYYY-MM-DD date string."""
    try:
        parts = value.split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
    except (ValueError, TypeError):
        err(f"Invalid date: {value}")


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    parts = [f'{task["id"]} [{status}] {task["title"]}']
    # priority suffix
    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")
    # tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


# ─── Commands ──────────────────────────────────────────────────────

def cmd_add(args, tasks, history):
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    positional = []
    while i < len(args):
        a = args[i]
        if a == "--priority":
            i += 1
            if i >= len(args):
                err("Missing value for --priority")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                err(f"Invalid priority: {priority}")
        elif a == "--tag":
            i += 1
            if i >= len(args):
                err("Missing value for --tag")
            tags.append(args[i])
        elif a == "--due":
            i += 1
            if i >= len(args):
                err("Missing value for --due")
            due = args[i]
            validate_date(due)
        elif a.startswith("--"):
            err(f"Unknown option: {a}")
        else:
            positional.append(a)
        i += 1

    if not positional:
        err("Missing title")
    title = " ".join(positional)

    new_task = {
        "id": next_id(tasks),
        "title": title,
        "done": False,
        "priority": priority,
        "tags": list(tags),
        "due": due,
    }

    # Snapshot for undo
    snapshot = {"tasks": copy.deepcopy(tasks), "next_id": next_id(tasks)}
    history.append(snapshot)

    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added {new_task['id']}")


def cmd_list(args, tasks, history):
    sort_priority = False
    tag_filter = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--sort":
            i += 1
            if i >= len(args):
                err("Missing value for --sort")
            if args[i] == "priority":
                sort_priority = True
            else:
                err(f"Unknown sort option: {args[i]}")
        elif a == "--tag":
            i += 1
            if i >= len(args):
                err("Missing value for --tag")
            tag_filter = args[i]
        elif a == "--overdue":
            overdue = True
        elif a == "--today":
            i += 1
            if i >= len(args):
                err("Missing value for --today")
            today = args[i]
            validate_date(today)
        elif a.startswith("--"):
            err(f"Unknown option: {a}")
        else:
            err(f"Unexpected argument: {a}")
        i += 1

    filtered = list(tasks)

    # Filter by tag
    if tag_filter is not None:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    # Overdue filter: only open tasks with due date before today
    if overdue:
        if today is None:
            today = date.today().isoformat()
        filtered = [t for t in filtered if not t["done"] and t.get("due") and t["due"] < today]

    # Sort by priority
    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
    else:
        for t in filtered:
            print(task_line(t))


def cmd_done(args, tasks, history):
    if not args:
        err("Missing task id")
    tid = int(args[0])
    task = _find_task(tid, tasks)
    if task is None:
        err(f"No such task: {tid}")

    # Snapshot for undo
    snapshot = {"tasks": copy.deepcopy(tasks), "next_id": next_id(tasks)}
    history.append(snapshot)

    task["done"] = True
    save_tasks(tasks)
    print(f"Done {tid}")


def cmd_delete(args, tasks, history):
    if not args:
        err("Missing task id")
    tid = int(args[0])
    task = _find_task(tid, tasks)
    if task is None:
        err(f"No such task: {tid}")

    # Snapshot for undo
    snapshot = {"tasks": copy.deepcopy(tasks), "next_id": next_id(tasks)}
    history.append(snapshot)

    tasks.remove(task)
    save_tasks(tasks)
    print(f"Deleted {tid}")


def cmd_edit(args, tasks, history):
    if not args:
        err("Missing task id")
    tid = int(args[0])
    task = _find_task(tid, tasks)
    if task is None:
        err(f"No such task: {tid}")

    new_title = None
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--title":
            i += 1
            if i >= len(args):
                err("Missing value for --title")
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            continue
        elif a.startswith("--"):
            err(f"Unknown option: {a}")
        i += 1

    if new_title is None:
        err("Missing --title")

    # Snapshot for undo
    snapshot = {"tasks": copy.deepcopy(tasks), "next_id": next_id(tasks)}
    history.append(snapshot)

    task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {tid}")


def cmd_search(args, tasks, history):
    if not args:
        err("Missing search text")
    text = " ".join(args).lower()
    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def cmd_export(args, tasks, history):
    fmt = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--format":
            i += 1
            if i >= len(args):
                err("Missing value for --format")
            fmt = args[i]
        elif a.startswith("--"):
            err(f"Unknown option: {a}")
        i += 1

    if fmt is None:
        err("Missing --format")
    if fmt not in ("json", "csv"):
        err(f"Unknown format: {fmt}")

    sorted_tasks = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in sorted_tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in sorted_tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due") or "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args, tasks, history):
    if args:
        err("stats takes no arguments")
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, tasks, history):
    if args:
        err("undo takes no arguments")
    if not history:
        err("Nothing to undo")

    snapshot = history.pop()
    tasks[:] = snapshot["tasks"]
    save_tasks(tasks)
    save_history(history)
    print("Undone")


# ─── Main ──────────────────────────────────────────────────────────

COMMANDS = {
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


def main():
    if len(sys.argv) < 2:
        err("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    if command not in COMMANDS:
        err(f"Unknown command: {command}")

    tasks = load_tasks()
    history = load_history()

    COMMANDS[command](sys.argv[2:], tasks, history)


if __name__ == "__main__":
    main()
