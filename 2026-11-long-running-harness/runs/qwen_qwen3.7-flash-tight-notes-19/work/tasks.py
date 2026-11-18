#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def push_undo(data):
    """Push current state onto undo stack before a mutating command."""
    data["undo_stack"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string."""
    try:
        parts = date_str.split("-")
        if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
        return date_str
    except (ValueError, TypeError):
        print("Invalid date: {}".format(date_str), file=sys.stderr)
        sys.exit(1)


def format_task_line(task):
    """Format a single task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])

    # Priority suffix
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"

    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)

    # Due date suffix
    if task.get("due"):
        line += " due:{}".format(task["due"])

    return line


def cmd_add(data, args):
    """Add a new task."""
    positional = args.get("_positional", [])
    if not positional:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(positional)

    priority = args.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)

    tags = args.get("tags", [])

    due = None
    if "due" in args:
        due = validate_date(args["due"])

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
    print("Added {}".format(task["id"]))


def cmd_list(data, args):
    """List tasks with optional filters and sorting."""
    sort = args.get("sort")
    tag_filter = args.get("tag")
    overdue = args.get("overdue", False)
    today_str = args.get("today")

    tasks = list(data["tasks"])

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        if today_str:
            today = validate_date(today_str)
        else:
            today = date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if sort == "priority":
        porder = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(data, args):
    """Mark a task as done."""
    positional = args.get("_positional", [])
    if not positional:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid task id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_undo(data)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(data, args):
    """Delete a task."""
    positional = args.get("_positional", [])
    if not positional:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid task id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(data, args):
    """Edit a task's title."""
    positional = args.get("_positional", [])
    if not positional:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid task id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    if "--title" not in args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    new_title_parts = positional[1:]
    new_title = " ".join(new_title_parts)

    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(data, args):
    """Search tasks by title (case-insensitive)."""
    positional = args.get("_positional", [])
    if not positional:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    search_text = " ".join(positional).lower()
    matches = [t for t in data["tasks"] if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(data, args):
    """Export tasks in JSON or CSV format."""
    fmt = args.get("format")
    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(export_data, indent=2))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            done_str = "true" if task["done"] else "false"
            print("{},{},{},{},{},{}".format(
                task["id"], task["title"], done_str,
                task.get("priority", "medium"), tags_str, due_str))
    else:
        print("Unknown format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(data, args):
    """Print task statistics."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(data, args):
    """Undo the most recent mutating command."""
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    previous = data["undo_stack"].pop()
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
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
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = args[0]
    raw_args = args[1:]

    # Parse keyword arguments
    kwargs = {}
    positional = []
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg == "--priority":
            i += 1
            kwargs["priority"] = raw_args[i]
        elif arg == "--tag":
            i += 1
            if "tags" not in kwargs:
                kwargs["tags"] = []
            kwargs["tags"].append(raw_args[i])
        elif arg == "--due":
            i += 1
            kwargs["due"] = raw_args[i]
        elif arg == "--sort":
            i += 1
            kwargs["sort"] = raw_args[i]
        elif arg == "--format":
            i += 1
            kwargs["format"] = raw_args[i]
        elif arg == "--title":
            pass  # handled below
        elif arg.startswith("--"):
            flag_name = arg[2:]
            if flag_name == "overdue":
                kwargs["overdue"] = True
            elif flag_name == "today":
                i += 1
                kwargs["today"] = raw_args[i]
            else:
                print("Unknown option: {}".format(arg), file=sys.stderr)
                sys.exit(1)
        else:
            positional.append(arg)
        i += 1

    kwargs["_positional"] = positional

    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](data, kwargs)


if __name__ == "__main__":
    main()
