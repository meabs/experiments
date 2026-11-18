#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and state from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and state to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print an error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def _get_task(data, tid):
    """Get task by integer id, handling string keys from JSON."""
    key = str(tid)
    return data["tasks"].get(key)


def task_line(task):
    """Format a task as a display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    """Handle the 'add' command."""
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)
    tid = data["next_id"]
    data["tasks"][tid] = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = tid + 1
    # Record undo history
    data["history"].append({
        "type": "add",
        "task_id": tid,
        "task": dict(data["tasks"][tid]),
    })
    save_data(data)
    print(f"Added {tid}")


def cmd_list(args, data):
    """Handle the 'list' command."""
    sort_by = None
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    today = date.today()
    if today_str:
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter by overdue
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and _parse_date(t["due"]) < today]

    # Sort
    if sort_by == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(args, data):
    """Handle the 'done' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = _get_task(data, tid)
    if task is None:
        error(f"No such task: {tid}")
    key = str(tid)
    old_task = dict(data["tasks"][key])
    data["tasks"][key]["done"] = True
    data["history"].append({
        "type": "done",
        "task_id": tid,
        "old_task": old_task,
    })
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Handle the 'delete' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = _get_task(data, tid)
    if task is None:
        error(f"No such task: {tid}")
    key = str(tid)
    old_task = dict(data["tasks"][key])
    del data["tasks"][key]
    data["history"].append({
        "type": "delete",
        "task_id": tid,
        "old_task": old_task,
    })
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Handle the 'edit' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = _get_task(data, tid)
    if task is None:
        error(f"No such task: {tid}")
    key = str(tid)

    new_title = None
    i = 1  # skip the id
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            # Collect all remaining args as the new title
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        error("--title is required")

    old_task = dict(data["tasks"][key])
    data["tasks"][key]["title"] = new_title
    data["history"].append({
        "type": "edit",
        "task_id": tid,
        "old_task": old_task,
    })
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Handle the 'search' command."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    matches = []
    for t in sorted(data["tasks"].values(), key=lambda x: x["id"]):
        if query in t["title"].lower():
            matches.append(t)
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def cmd_export(args, data):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("--format is required")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f'{t["id"]},{t["title"]},{done_str},{t["priority"]},{tags_str},{due_str}')
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args, data):
    """Handle the 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle the 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")

    last = data["history"].pop()
    htype = last["type"]

    if htype == "add":
        tid = last["task_id"]
        del data["tasks"][tid]
        data["next_id"] = tid
    elif htype == "done":
        tid = last["task_id"]
        data["tasks"][str(tid)]["done"] = last["old_task"]["done"]
    elif htype == "delete":
        tid = last["task_id"]
        data["tasks"][str(tid)] = last["old_task"]
    elif htype == "edit":
        tid = last["task_id"]
        data["tasks"][str(tid)] = last["old_task"]

    save_data(data)
    print("Undone")


def _parse_date(s):
    """Parse a YYYY-MM-DD string to a date object."""
    parts = s.split("-")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
