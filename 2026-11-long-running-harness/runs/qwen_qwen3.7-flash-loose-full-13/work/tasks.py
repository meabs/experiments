#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    new_tasks = {}
    for tid, task in data["tasks"].items():
        int_id = int(tid)
        task["id"] = int_id
        new_tasks[int_id] = task
    data["tasks"] = new_tasks
    return data


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def record_undo(data):
    """Record a snapshot of current state for undo."""
    snapshot_tasks = {tid: dict(task) for tid, task in data["tasks"].items()}
    data["history"].append({
        "tasks": snapshot_tasks,
        "next_id": data["next_id"],
    })
    save_data(data)


def parse_args(args):
    """Parse command-line arguments into a dict of options."""
    opts = {}
    i = 0
    positional = []
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            opts["priority"] = args[i + 1]
            i += 2
        elif arg == "--tag":
            opts.setdefault("tags", []).append(args[i + 1])
            i += 2
        elif arg == "--due":
            opts["due"] = args[i + 1]
            i += 2
        elif arg == "--title":
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            opts["title"] = " ".join(title_parts)
        else:
            positional.append(arg)
            i += 1
    opts["_positional"] = positional
    return opts


def format_task_line(task):
    """Format a task for display in list/search output."""
    marker = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), marker, task["title"]]
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    tags = task.get("tags", [])
    if tags:
        parts.append(" ".join("#" + t for t in tags))
    if task.get("due"):
        parts.append("due:" + task["due"])
    return " ".join(parts)


def cmd_add(args):
    """Handle the 'add' command."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(positional)
    priority = opts.get("priority", "medium")
    tags = opts.get("tags", [])
    due = opts.get("due", None)

    if priority not in ("high", "medium", "low"):
        print("Invalid priority: " + priority, file=sys.stderr)
        sys.exit(1)

    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            print("Invalid date: " + due, file=sys.stderr)
            sys.exit(1)

    data = load_data()
    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = task_id + 1
    record_undo(data)
    print("Added " + str(task_id))


def cmd_list(args):
    """Handle the 'list' command."""
    opts = parse_args(args)
    positional = opts["_positional"]
    sort_by = None
    filter_tag = None
    show_overdue = False
    today_str = None

    i = 0
    while i < len(positional):
        arg = positional[i]
        if arg == "--sort":
            sort_by = positional[i + 1]
            i += 2
        elif arg == "--tag":
            filter_tag = positional[i + 1]
            i += 2
        elif arg == "--overdue":
            show_overdue = True
            i += 1
        elif arg == "--today":
            today_str = positional[i + 1]
            i += 2
        else:
            i += 1

    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if show_overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    if not tasks:
        print("No tasks")
        return

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(positional[0])
    except ValueError:
        print("No such task: " + positional[0], file=sys.stderr)
        sys.exit(1)

    data = load_data()
    if task_id not in data["tasks"]:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)

    data["tasks"][task_id]["done"] = True
    record_undo(data)
    print("Done " + str(task_id))


def cmd_delete(args):
    """Handle the 'delete' command."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(positional[0])
    except ValueError:
        print("No such task: " + positional[0], file=sys.stderr)
        sys.exit(1)

    data = load_data()
    if task_id not in data["tasks"]:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)

    del data["tasks"][task_id]
    record_undo(data)
    print("Deleted " + str(task_id))


def cmd_edit(args):
    """Handle the 'edit' command."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(positional[0])
    except ValueError:
        print("No such task: " + positional[0], file=sys.stderr)
        sys.exit(1)

    if "title" not in opts:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    if task_id not in data["tasks"]:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)

    data["tasks"][task_id]["title"] = opts["title"]
    record_undo(data)
    print("Edited " + str(task_id))


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    opts = parse_args(args)
    fmt = opts.get("_positional", ["json"])[0] if opts.get("_positional") else "json"

    data = load_data()
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
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(str(t["id"]) + "," + t["title"] + ",true" if t["done"] else "false," + t["priority"] + "," + tags_str + "," + due_str)
    else:
        print("Unknown format: " + fmt, file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(list(tasks))
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total))


def cmd_undo(args):
    """Handle the 'undo' command."""
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
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
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: " + command, file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
