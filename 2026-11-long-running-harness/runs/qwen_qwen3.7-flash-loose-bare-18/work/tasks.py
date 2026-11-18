#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if "undo_history" not in data:
        data["undo_history"] = []
    return data


def save_data(data):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    # Priority suffix (high/low only; medium shows nothing)
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += " #" + tag
    # Due date suffix
    if task.get("due"):
        line += " due:" + task["due"]
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def _snapshot(data):
    """Create a JSON snapshot of current mutable state for undo."""
    return json.dumps({"tasks": list(data["tasks"]), "next_id": data["next_id"]})


def cmd_add(args):
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
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(priority))
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: {}".format(due_str))
            due = due_str
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)

    # Snapshot before mutation
    snap = _snapshot(data)

    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] = task_id + 1
    data["undo_history"].append(snap)

    save_data(data)
    print("Added {}".format(task_id))


def cmd_list(args):
    """Handle the 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            sort_option = args[i + 1]
            if sort_option == "priority":
                sort_priority = True
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    today = date.today()
    if today_str:
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error("Invalid date: {}".format(today_str))

    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter: only open tasks with due date before today
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task ID: {}".format(args[0]))

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error("No such task: {}".format(task_id))

    # Snapshot before mutation
    snap = _snapshot(data)

    task["done"] = True
    data["undo_history"].append(snap)
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task ID: {}".format(args[0]))

    task_idx = None
    for idx, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            task_idx = idx
            break

    if task_idx is None:
        error("No such task: {}".format(task_id))

    # Snapshot before mutation
    snap = _snapshot(data)

    del data["tasks"][task_idx]
    data["undo_history"].append(snap)
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    """Handle the 'edit' command."""
    task_id = None
    new_title = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            if task_id is None:
                error("Missing task ID for edit")
            new_title = " ".join(args[i + 1:])
            break
        else:
            if task_id is None:
                try:
                    task_id = int(arg)
                except ValueError:
                    error("Invalid task ID: {}".format(arg))
            i += 1
            continue
        i += 2

    if task_id is None:
        error("Missing task ID")
    if new_title is None:
        error("Missing --title")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error("No such task: {}".format(task_id))

    # Snapshot before mutation
    snap = _snapshot(data)

    task["title"] = new_title
    data["undo_history"].append(snap)
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    matches = []
    for t in data["tasks"]:
        if query in t["title"].lower():
            matches.append(t)

    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
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
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str))
    else:
        error("Unknown format: {}".format(fmt))


def cmd_stats(args):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    """Handle the 'undo' command."""
    if not data["undo_history"]:
        error("Nothing to undo")

    previous_state = json.loads(data["undo_history"].pop())
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
    save_data(data)
    print("Undone")


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
    global data
    data = load_data()

    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error("Unknown command: {}".format(command))

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
