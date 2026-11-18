#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    """Load tasks from tasks.json, returning (tasks, next_id)."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data["tasks"], data["next_id"]


def save_tasks(tasks, next_id):
    """Save tasks and next_id to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    """Load undo history from undo_history.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    """Save undo history to undo_history.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print an error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    done_marker = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), done_marker, task["title"]]
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium has no suffix
    # Tags suffix
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def parse_args(args):
    """Parse command-line arguments into command and options."""
    if not args:
        error("No command given")
    command = args[0]
    opts = {"_positional": []}
    i = 1
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            opts["--priority"] = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            opts.setdefault("--tag", []).append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            opts["--due"] = args[i + 1]
            i += 2
        elif args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            opts["--sort"] = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            opts["--overdue"] = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            opts["--today"] = args[i + 1]
            i += 2
        elif args[i] == "--title":
            title_parts = []
            j = i + 1
            while j < len(args):
                arg = args[j]
                if arg.startswith("--"):
                    break
                title_parts.append(arg)
                j += 1
            if not title_parts:
                error("Missing value for --title")
            opts["--title"] = " ".join(title_parts)
            i = j
        elif args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            opts["--format"] = args[i + 1]
            i += 2
        elif args[i].startswith("--"):
            # Unknown flag, skip it and its value
            i += 1
        else:
            opts["_positional"].append(args[i])
            i += 1
    return command, opts


def cmd_add(tasks, next_id, opts):
    """Handle the 'add' command."""
    pos = opts["_positional"]
    if not pos:
        error("Missing title")
    title = " ".join(pos)

    priority = opts.get("--priority", "medium")
    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")

    tags = opts.get("--tag", [])
    due = opts.get("--due", None)

    if due:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    next_id += 1
    save_tasks(tasks, next_id)
    print(f"Added {task['id']}")


def cmd_list(tasks, next_id, opts):
    """Handle the 'list' command."""
    filtered = list(tasks)

    # Filter by tag using --tag
    if "--tag" in opts:
        tag_filter = opts["--tag"][0] if opts["--tag"] else None
        if tag_filter:
            filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    # Overdue filter
    if opts.get("--overdue"):
        today_str = opts.get("--today", date.today().isoformat())
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    sort_key = opts.get("--sort")
    if sort_key == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    elif sort_key:
        error(f"Unknown sort option: {sort_key}")

    if not filtered:
        print("No tasks")
    else:
        for task in filtered:
            print(task_line(task))


def cmd_done(tasks, next_id, opts):
    """Handle the 'done' command."""
    pos = opts["_positional"]
    if not pos:
        error("Missing task id")
    try:
        task_id = int(pos[0])
    except ValueError:
        error(f"No such task: {pos[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    task["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(tasks, next_id, opts):
    """Handle the 'delete' command."""
    pos = opts["_positional"]
    if not pos:
        error("Missing task id")
    try:
        task_id = int(pos[0])
    except ValueError:
        error(f"No such task: {pos[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    tasks.remove(task)
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(tasks, next_id, opts):
    """Handle the 'edit' command."""
    pos = opts["_positional"]
    if not pos:
        error("Missing task id")
    try:
        task_id = int(pos[0])
    except ValueError:
        error(f"No such task: {pos[0]}")

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    new_title = opts.get("--title")
    if new_title is None:
        error("Missing --title")

    task["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(tasks, next_id, opts):
    """Handle the 'search' command."""
    pos = opts["_positional"]
    if not pos:
        error("Missing search text")
    text = " ".join(pos).lower()

    matches = [t for t in tasks if text in t["title"].lower()]
    # Already in id order since we iterate in order
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(tasks, next_id, opts):
    """Handle the 'export' command."""
    fmt = opts.get("--format")
    if fmt is None:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    if fmt == "json":
        export_data = []
        for t in sorted(tasks, key=lambda x: x["id"]):
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in sorted(tasks, key=lambda x: x["id"]):
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')


def cmd_stats(tasks, next_id, opts):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(tasks, next_id, opts):
    """Handle the 'undo' command."""
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    last_snapshot = history.pop()
    save_undo_history(history)
    save_tasks(last_snapshot["tasks"], last_snapshot["next_id"])
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
        error("No command given")

    command, opts = parse_args(args)

    tasks, next_id = load_tasks()

    if command == "undo":
        cmd_undo(tasks, next_id, opts)
        return

    # Record snapshot before mutation
    if command in ("add", "done", "delete", "edit"):
        import copy
        history = load_undo_history()
        history.append({
            "tasks": copy.deepcopy(tasks),
            "next_id": next_id,
        })
        save_undo_history(history)

    handler = COMMANDS.get(command)
    if handler is None:
        error(f"Unknown command: {command}")

    handler(tasks, next_id, opts)


if __name__ == "__main__":
    main()
