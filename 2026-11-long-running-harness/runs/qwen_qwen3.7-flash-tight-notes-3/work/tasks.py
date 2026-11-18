#!/usr/bin/env python3
"""A command-line task manager."""

import copy
import csv
import io
import json
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"tasks": [], "next_id": 1}


def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(data):
    """Save a snapshot of current data for undo."""
    history = load_undo_history()
    history.append(copy.deepcopy(data))
    if len(history) > 1000:
        history = history[-1000:]
    save_undo_history(history)


def cmd_undo():
    """Revert the most recent mutating command."""
    history = load_undo_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = history.pop()
    save_undo_history(history)
    save_tasks(prev_state)
    print("Undone")


def format_task_line(task):
    """Format a task into its display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    title = task["title"]
    parts = [f"{tid} {status} {title}"]
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")
    tags = task.get("tags", [])
    if tags:
        parts.append(" ".join(f"#{t}" for t in tags))
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def cmd_add(args, data):
    """Add a new task."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    found_title = False
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                date.fromisoformat(due_str)
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            if not found_title:
                found_title = True
            title_parts.append(arg)
            i += 1
    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    push_undo(data)
    new_task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] += 1
    data["tasks"].append(new_task)
    save_tasks(data)
    print(f"Added {new_task['id']}")


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = _find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task["done"] = True
    save_tasks(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = _find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_tasks(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = _find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title_parts = []
    i = 1
    found_title_flag = False
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            found_title_flag = True
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
        else:
            i += 1
    if not new_title_parts:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(new_title_parts)
    push_undo(data)
    task["title"] = new_title
    save_tasks(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title text (case-insensitive)."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    if fmt == "json":
        output = []
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
            writer.writerow([
                task["id"],
                task["title"],
                str(task["done"]).lower(),
                task.get("priority", "medium"),
                ";".join(task.get("tags", [])),
                task.get("due", ""),
            ])
        print(buf.getvalue(), end="")
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Print task statistics."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def _find_task(data, task_id):
    """Find a task by id, return None if not found."""
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    data = load_tasks()
    if command == "add":
        cmd_add(args, data)
    elif command == "list":
        cmd_list(args, data)
    elif command == "done":
        cmd_done(args, data)
    elif command == "delete":
        cmd_delete(args, data)
    elif command == "edit":
        cmd_edit(args, data)
    elif command == "search":
        cmd_search(args, data)
    elif command == "export":
        cmd_export(args, data)
    elif command == "stats":
        cmd_stats(args, data)
    elif command == "undo":
        cmd_undo()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
