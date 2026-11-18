#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and history from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": {}, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if "next_id" not in data:
        data["next_id"] = max(data["tasks"].keys()) + 1 if data["tasks"] else 1
    if "history" not in data:
        data["history"] = []
    data["next_id"] = int(data["next_id"])
    tasks = {}
    for k, v in data["tasks"].items():
        tasks[int(k)] = v
    data["tasks"] = tasks
    return data


def save_data(data):
    """Save tasks and history to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def validate_date(value):
    """Validate a YYYY-MM-DD date string."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_task_line(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def parse_args(args):
    """Parse command-line arguments into options and positional args."""
    options = {}
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if key in ("tag", "title", "priority", "due", "format", "today"):
                if key == "title":
                    options["title_parts"] = args[i + 1:]
                    break
                if i + 1 < len(args):
                    val = args[i + 1]
                    if key == "tag":
                        options.setdefault("tags", []).append(val)
                    elif key == "format":
                        options["format"] = val
                    elif key == "today":
                        options["today"] = val
                    else:
                        options[key] = val
                    i += 2
                else:
                    error(f"Missing value for --{key}")
            elif key == "sort":
                if i + 1 < len(args):
                    options["sort"] = args[i + 1]
                    i += 2
                else:
                    error("Missing value for --sort")
            elif key == "overdue":
                options["overdue"] = True
                i += 1
            else:
                error(f"Unknown option: --{arg}")
        else:
            positional.append(arg)
            i += 1
    if "title_parts" in options:
        options["title"] = " ".join(options["title_parts"])
        del options["title_parts"]
    return options, positional


def deep_snapshot(tasks_dict):
    """Create a deep copy of tasks for undo snapshots."""
    snapshot = {}
    for tid, task in tasks_dict.items():
        snapshot[tid] = {
            "id": task["id"],
            "title": task["title"],
            "done": task["done"],
            "priority": task["priority"],
            "tags": list(task["tags"]),
            "due": task["due"],
        }
    return snapshot


def cmd_add(args, data):
    """Add a new task."""
    options, positional = parse_args(args)
    if not positional:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = positional[0]

    priority = options.get("priority", "medium")
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        error(f"Invalid priority: {priority}")

    tags = options.get("tags", [])
    due = options.get("due", None)
    if due is not None:
        if not validate_date(due):
            error(f"Invalid date: {due}")

    # Snapshot BEFORE adding the task
    prev_tasks = deep_snapshot(data["tasks"])
    prev_next_id = data["next_id"]

    task_id = data["next_id"]
    data["next_id"] += 1

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][task_id] = task

    data["history"].append({
        "action": "add",
        "prev_tasks": prev_tasks,
        "prev_next_id": prev_next_id,
    })

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """List tasks."""
    options, positional = parse_args(args)
    tasks = list(data["tasks"].values())

    if "tags" in options:
        filter_tag = options["tags"][0]
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if options.get("overdue"):
        today_str = options.get("today", date.today().isoformat())
        try:
            datetime.strptime(today_str, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_str]

    if options.get("sort") == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    options, positional = parse_args(args)
    if not positional:
        error("Usage: done ID")
    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"Invalid task id: {positional[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Snapshot BEFORE modifying the task
    prev_tasks = deep_snapshot(data["tasks"])
    prev_next_id = data["next_id"]

    data["history"].append({
        "action": "done",
        "prev_tasks": prev_tasks,
        "prev_next_id": prev_next_id,
    })

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    options, positional = parse_args(args)
    if not positional:
        error("Usage: delete ID")
    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"Invalid task id: {positional[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Snapshot BEFORE deleting the task
    prev_tasks = deep_snapshot(data["tasks"])
    prev_next_id = data["next_id"]

    data["history"].append({
        "action": "delete",
        "prev_tasks": prev_tasks,
        "prev_next_id": prev_next_id,
    })

    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    options, positional = parse_args(args)
    if not positional:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"Invalid task id: {positional[0]}")

    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    if "title" not in options:
        error("Usage: edit ID --title NEW TITLE")

    new_title = options["title"]

    # Snapshot BEFORE editing the task
    prev_tasks = deep_snapshot(data["tasks"])
    prev_next_id = data["next_id"]

    data["history"].append({
        "action": "edit",
        "prev_tasks": prev_tasks,
        "prev_next_id": prev_next_id,
    })

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title text."""
    options, positional = parse_args(args)
    if not positional:
        error("Usage: search TEXT")
    query = " ".join(positional).lower()

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    options, positional = parse_args(args)
    fmt = options.get("format")
    if fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
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
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Print task statistics."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the most recent mutating command."""
    if not data["history"]:
        error("Nothing to undo")

    entry = data["history"].pop()
    data["tasks"] = entry["prev_tasks"]
    data["next_id"] = entry["prev_next_id"]
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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
