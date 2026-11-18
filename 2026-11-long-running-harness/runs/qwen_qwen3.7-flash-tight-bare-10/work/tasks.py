#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime
from copy import deepcopy

DATA_FILE = "tasks.json"


def load_data():
    """Load data from tasks.json. Create if not exists."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"next_id": 1, "tasks": {}, "history": []}


def save_data(data):
    """Save data to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def make_task_line(task):
    """Build a display line for a task."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f'{task["id"]} {status} {task["title"]}']
    # priority suffix (medium shows nothing)
    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")
    # tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # due date suffix
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def snapshot(data):
    """Create a deep copy of the current state for undo history."""
    return {
        "next_id": data["next_id"],
        "tasks": deepcopy(data["tasks"]),
    }


def do_add(args, data):
    """Handle 'add' command."""
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
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.extend(arg.split())
            i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)

    # Save state for undo
    data["history"].append(snapshot(data))

    tid = data["next_id"]
    data["next_id"] += 1
    tid_str = str(tid)
    data["tasks"][tid_str] = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_data(data)
    print(f"Added {tid}")


def do_list(args, data):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_date = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            sort_priority = args[i + 1] == "priority"
            i += 2
        elif arg == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today" and i + 1 < len(args):
            today_date = args[i + 1]
            i += 2
        else:
            i += 1

    if today_date is not None:
        try:
            today_parsed = datetime.strptime(today_date, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_date}")
    else:
        today_parsed = date.today()

    tasks = list(data["tasks"].values())

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue
    if overdue:
        filtered = []
        for t in tasks:
            if not t["done"] and t.get("due"):
                try:
                    due_d = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_d < today_parsed:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(make_task_line(task))


def do_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tid_str = str(tid)
    if tid_str not in data["tasks"]:
        error(f"No such task: {tid}")

    # Save state for undo
    data["history"].append(snapshot(data))

    data["tasks"][tid_str]["done"] = True
    save_data(data)
    print(f"Done {tid}")


def do_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tid_str = str(tid)
    if tid_str not in data["tasks"]:
        error(f"No such task: {tid}")

    # Save state for undo
    data["history"].append(snapshot(data))

    del data["tasks"][tid_str]
    save_data(data)
    print(f"Deleted {tid}")


def do_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Missing task id")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tid_str = str(tid)
    if tid_str not in data["tasks"]:
        error(f"No such task: {tid}")

    new_title = None
    i = 1  # skip the id
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            new_title = args[i + 1]
            i += 2
        else:
            i += 1

    if new_title is None:
        error("Missing --title")

    # Save state for undo
    data["history"].append(snapshot(data))

    data["tasks"][tid_str]["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def do_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(make_task_line(task))


def do_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt != "json" and fmt != "csv":
        error(f"Invalid format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            lines.append(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
        print("\n".join(lines))


def do_stats(args, data):
    """Handle 'stats' command."""
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(list(tasks))
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def do_undo(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")

    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
