#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def parse_args(argv):
    """Parse command line arguments into a structured dict.
    
    argv should be sys.argv[1:] - the first element is the subcommand.
    Returns (command, args_dict).
    """
    if not argv:
        error("No command specified")

    command = argv[0]
    rest = argv[1:]

    args = {"positional": [], "flags": {}}
    i = 0
    while i < len(rest):
        token = rest[i]
        if token.startswith("--"):
            key = token[2:]
            if key == "tag":
                if i + 1 >= len(rest):
                    error("--tag requires a value")
                args["flags"].setdefault("tag", []).append(rest[i + 1])
                i += 2
            elif key in ("due", "format", "today", "sort", "priority"):
                i += 1
                if i >= len(rest):
                    error(f"--{key} requires a value")
                args["flags"][key] = rest[i]
                i += 1
            elif key == "overdue":
                args["flags"]["overdue"] = True
                i += 1
            elif key == "title":
                i += 1
                title_parts = []
                while i < len(rest) and not rest[i].startswith("--"):
                    title_parts.append(rest[i])
                    i += 1
                if not title_parts:
                    error("--title requires a value")
                args["flags"]["title"] = " ".join(title_parts)
            else:
                error(f"Unknown option: {token}")
        else:
            args["positional"].append(token)
            i += 1

    return command, args


def snapshot_tasks(tasks_dict):
    """Deep copy tasks dict for undo history."""
    return json.loads(json.dumps(tasks_dict))


# ---------- Commands ----------

def cmd_add(data, args):
    """Add a new task."""
    if not args["positional"]:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(args["positional"])
    priority = args["flags"].get("priority", "medium")
    tags = args["flags"].get("tag", [])
    due = args["flags"].get("due", None)

    # Validate priority
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        error(f"Invalid priority: {priority}")

    # Validate date
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    # Snapshot BEFORE mutation
    data["history"].append({
        "tasks": snapshot_tasks(data["tasks"]),
        "next_id": data["next_id"],
    })

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

    data["tasks"][str(task_id)] = task
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(data, args):
    """List tasks."""
    sort_by = args["flags"].get("sort", None)
    tag_filters = args["flags"].get("tag", [])
    overdue = args["flags"].get("overdue", False)
    today_str = args["flags"].get("today", None)

    tasks = list(data["tasks"].values())

    if not tasks:
        print("No tasks")
        return

    # Filter by tag(s) - must match ALL provided tags
    if tag_filters:
        tasks = [t for t in tasks if all(tf in t.get("tags", []) for tf in tag_filters)]

    # Overdue filter - only open tasks with a due date before today
    if overdue:
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    if not tasks:
        print("No tasks")
        return

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for task in tasks:
        print(format_task(task))


def cmd_done(data, args):
    """Mark a task as done."""
    if not args["positional"]:
        error("Usage: done ID")

    task_id = int(args["positional"][0])
    task_key = str(task_id)

    if task_key not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Snapshot before mutation
    data["history"].append({
        "tasks": snapshot_tasks(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"][task_key]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(data, args):
    """Delete a task."""
    if not args["positional"]:
        error("Usage: delete ID")

    task_id = int(args["positional"][0])
    task_key = str(task_id)

    if task_key not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Snapshot before mutation
    data["history"].append({
        "tasks": snapshot_tasks(data["tasks"]),
        "next_id": data["next_id"],
    })

    del data["tasks"][task_key]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(data, args):
    """Edit a task's title."""
    if not args["positional"]:
        error("Usage: edit ID --title NEW TITLE")

    task_id = int(args["positional"][0])
    task_key = str(task_id)

    if task_key not in data["tasks"]:
        error(f"No such task: {task_id}")

    if "title" not in args["flags"]:
        error("Usage: edit ID --title NEW TITLE")

    # Snapshot before mutation
    data["history"].append({
        "tasks": snapshot_tasks(data["tasks"]),
        "next_id": data["next_id"],
    })

    data["tasks"][task_key]["title"] = args["flags"]["title"]
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(data, args):
    """Search tasks by title (case-insensitive)."""
    if not args["positional"]:
        error("Usage: search TEXT")

    query = " ".join(args["positional"]).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(data, args):
    """Export tasks in JSON or CSV format."""
    fmt = args["flags"].get("format")
    if not fmt:
        error("Usage: export --format json|csv")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(f'{t["id"]},{t["title"]},{done_str},{t["priority"]},{tags_str},{due_str}')


def cmd_stats(data, args):
    """Print statistics about tasks."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(data, args):
    """Undo the most recent mutating command."""
    if not data["history"]:
        error("Nothing to undo")

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
    argv = sys.argv[1:]
    if not argv:
        error("No command specified")

    command, args = parse_args(argv)

    data = load_data()
    handler = COMMANDS.get(command)
    if not handler:
        error(f"Unknown command: {command}")

    handler(data, args)


if __name__ == "__main__":
    main()
