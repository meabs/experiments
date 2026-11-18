#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium shows no suffix
    # Tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def parse_args(argv):
    """Parse command-line arguments into a structured dict."""
    args = {
        "command": None,
        "positional": [],
        "flags": {},
        "repeated_flags": {},
    }
    i = 0
    if i < len(argv):
        args["command"] = argv[i]
        i += 1

    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                val = argv[i + 1]
                i += 2
            else:
                val = True
                i += 1
            if key in args["repeated_flags"]:
                args["repeated_flags"][key].append(val)
            elif key in args["flags"]:
                # Convert single value to list
                args["flags"][key] = [args["flags"][key], val]
            else:
                args["flags"][key] = val
        else:
            args["positional"].append(arg)
            i += 1
    return args


def cmd_add(args, data):
    """Handle the 'add' command."""
    if not args["positional"]:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    # Parse priority
    priority = "medium"
    if "priority" in args["flags"]:
        priority = args["flags"]["priority"]
        if priority not in ("high", "medium", "low"):
            print(f"Invalid priority: {priority}", file=sys.stderr)
            sys.exit(1)

    # Parse tags (repeatable)
    tags = []
    if "tag" in args["repeated_flags"]:
        tags = args["repeated_flags"]["tag"]

    # Parse due date
    due = None
    if "due" in args["flags"]:
        due_val = args["flags"]["due"]
        try:
            datetime.strptime(due_val, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {due_val}", file=sys.stderr)
            sys.exit(1)
        due = due_val

    # Save state before mutation
    data["history"].append({
        "type": "add",
        "task_id": data["next_id"],
        "prev_tasks": copy.deepcopy(data["tasks"]),
        "prev_next_id": data["next_id"],
    })

    task = {
        "id": data["next_id"],
        "title": " ".join(args["positional"]),
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    """Handle the 'list' command."""
    tasks = data["tasks"]

    # Filter by tag
    if "tag" in args["flags"]:
        filter_tag = args["flags"]["tag"]
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if "overdue" in args["flags"]:
        today_str = args["flags"].get("today", date.today().isoformat())
        try:
            datetime.strptime(today_str, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if args["flags"].get("sort") == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks_sorted = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks_sorted = sorted(tasks, key=lambda t: t["id"])

    for task in tasks_sorted:
        print(task_line(task))


def cmd_done(args, data):
    """Handle the 'done' command."""
    if not args["positional"]:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args["positional"][0])
    except ValueError:
        print(f"No such task: {args['positional'][0]}", file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state before mutation
    data["history"].append({
        "type": "done",
        "task_id": task_id,
        "prev_tasks": copy.deepcopy(data["tasks"]),
        "prev_next_id": data["next_id"],
    })

    task["done"] = True

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle the 'delete' command."""
    if not args["positional"]:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args["positional"][0])
    except ValueError:
        print(f"No such task: {args['positional'][0]}", file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save state before mutation
    data["history"].append({
        "type": "delete",
        "task_id": task_id,
        "deleted_task": copy.deepcopy(task),
        "prev_tasks": copy.deepcopy(data["tasks"]),
        "prev_next_id": data["next_id"],
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle the 'edit' command."""
    if not args["positional"]:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args["positional"][0])
    except ValueError:
        print(f"No such task: {args['positional'][0]}", file=sys.stderr)
        sys.exit(1)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    if "title" not in args["flags"]:
        print("Error: missing --title", file=sys.stderr)
        sys.exit(1)

    new_title = args["flags"]["title"]

    # Save state before mutation
    data["history"].append({
        "type": "edit",
        "task_id": task_id,
        "old_title": task["title"],
        "prev_tasks": copy.deepcopy(data["tasks"]),
        "prev_next_id": data["next_id"],
    })

    task["title"] = new_title

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle the 'search' command."""
    if not args["positional"]:
        print("Error: missing search text", file=sys.stderr)
        sys.exit(1)

    search_text = " ".join(args["positional"]).lower()
    matches = [t for t in data["tasks"] if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Handle the 'export' command."""
    fmt = args["flags"].get("format")
    if fmt not in ("json", "csv"):
        print("Error: --format must be json or csv", file=sys.stderr)
        sys.exit(1)

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
        print(json.dumps(export_data, indent=2))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')


def cmd_stats(args, data):
    """Handle the 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle the 'undo' command."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    entry = data["history"].pop()
    data["tasks"] = entry["prev_tasks"]
    data["next_id"] = entry["prev_next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Error: missing command", file=sys.stderr)
        sys.exit(1)

    parsed = parse_args(sys.argv[1:])
    command = parsed["command"]

    if command not in ("add", "list", "done", "delete", "edit", "search", "export", "stats", "undo"):
        print(f"Error: unknown command '{command}'", file=sys.stderr)
        sys.exit(1)

    data = load_data()

    commands = {
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

    commands[command](parsed, data)


if __name__ == "__main__":
    main()
