#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
import copy
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    """Load tasks from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1}


def save_tasks(data):
    """Save tasks to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    """Load undo history."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo(history):
    """Save undo history."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    tid = task["id"]
    status = "x" if task["done"] else " "
    title = task["title"]
    suffixes = []

    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        suffixes.append("(high)")
    elif priority == "low":
        suffixes.append("(low)")

    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        suffixes.append("#" + tag)

    # Due date suffix
    due = task.get("due")
    if due:
        suffixes.append("due:" + due)

    line = f"{tid} [{status}] {title}"
    if suffixes:
        line += " " + " ".join(suffixes)
    return line


def parse_args(argv):
    """Parse command line arguments into a structured form."""
    if not argv:
        return None, [], {}

    command = argv[0]
    args = argv[1:]

    positional = []
    flags = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            flag_name = arg[2:]
            if flag_name == "tag":
                if flag_name not in flags:
                    flags[flag_name] = []
                i += 1
                if i < len(args):
                    flags[flag_name].append(args[i])
            elif flag_name == "title":
                parts = []
                i += 1
                while i < len(args) and not args[i].startswith("--"):
                    parts.append(args[i])
                    i += 1
                flags[flag_name] = " ".join(parts)
                continue
            elif flag_name in ("priority", "due", "format", "today"):
                i += 1
                if i < len(args):
                    flags[flag_name] = args[i]
                else:
                    error(f"Missing value for --{flag_name}")
            elif flag_name in ("sort",):
                i += 1
                if i < len(args):
                    flags[flag_name] = args[i]
                else:
                    error(f"Missing value for --{flag_name}")
            else:
                flags[flag_name] = True
        else:
            positional.append(arg)
        i += 1

    return command, positional, flags


def cmd_add(tasks_data, positional, flags):
    """Add a new task."""
    if not positional:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(positional)

    priority = flags.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")

    tags = flags.get("tag", [])

    due = flags.get("due")
    if due is not None:
        try:
            date.fromisoformat(due)
        except ValueError:
            error(f"Invalid date: {due}")

    next_id = tasks_data["next_id"]
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks_data["tasks"][str(next_id)] = task
    tasks_data["next_id"] = next_id + 1

    save_tasks(tasks_data)
    print(f"Added {next_id}")


def cmd_list(tasks_data, positional, flags):
    """List tasks with optional filtering/sorting."""
    tasks = list(tasks_data["tasks"].values())

    tag_filter = flags.get("tag")
    if tag_filter is not None:
        tasks = [t for t in tasks if any(tf in t.get("tags", []) for tf in tag_filter)]

    overdue = flags.get("overdue")
    today_flag = flags.get("today")
    if overdue is True or today_flag is not None:
        if today_flag is not None:
            try:
                today = date.fromisoformat(today_flag)
            except ValueError:
                error(f"Invalid date: {today_flag}")
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today
        ]

    sort_by = flags.get("sort")
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(tasks_data, positional, flags):
    """Mark a task as done."""
    if not positional:
        error("Usage: done ID")

    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"No such task: {positional[0]}")

    key = str(task_id)
    if key not in tasks_data["tasks"]:
        error(f"No such task: {task_id}")

    tasks_data["tasks"][key]["done"] = True
    save_tasks(tasks_data)
    print(f"Done {task_id}")


def cmd_delete(tasks_data, positional, flags):
    """Delete a task."""
    if not positional:
        error("Usage: delete ID")

    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"No such task: {positional[0]}")

    key = str(task_id)
    if key not in tasks_data["tasks"]:
        error(f"No such task: {task_id}")

    del tasks_data["tasks"][key]
    save_tasks(tasks_data)
    print(f"Deleted {task_id}")


def cmd_edit(tasks_data, positional, flags):
    """Edit a task's title."""
    if not positional:
        error("Usage: edit ID --title NEW TITLE")

    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"No such task: {positional[0]}")

    key = str(task_id)
    if key not in tasks_data["tasks"]:
        error(f"No such task: {task_id}")

    if "title" not in flags:
        error("Usage: edit ID --title NEW TITLE")

    new_title = flags["title"]
    tasks_data["tasks"][key]["title"] = new_title
    save_tasks(tasks_data)
    print(f"Edited {task_id}")


def cmd_search(tasks_data, positional, flags):
    """Search tasks by title (case-insensitive)."""
    if not positional:
        error("Usage: search TEXT")

    query = " ".join(positional).lower()
    tasks = [t for t in tasks_data["tasks"].values() if query in t["title"].lower()]
    tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No matches")
        return

    for task in tasks:
        print(task_line(task))


def cmd_export(tasks_data, positional, flags):
    """Export tasks in JSON or CSV format."""
    fmt = flags.get("format")
    if not fmt:
        error("Usage: export --format json|csv")

    tasks = sorted(tasks_data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for task in tasks:
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
        lines = ["id,title,done,priority,tags,due"]
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            done_str = "true" if task["done"] else "false"
            lines.append(f'{task["id"]},{task["title"]},{done_str},{task.get("priority", "medium")},{tags_str},{due_str}')
        print("\n".join(lines))
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(tasks_data, positional, flags):
    """Print task statistics."""
    tasks = list(tasks_data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(tasks_data, positional, flags):
    """Undo the most recent mutating command."""
    history = load_undo()
    if not history:
        error("Nothing to undo")

    previous_state = history.pop()
    save_undo(history)
    save_tasks(previous_state)
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
        error("Usage: python3 tasks.py <command> [args]")

    command, positional, flags = parse_args(argv)

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    # For commands that modify state, we need to record undo state BEFORE executing
    if command in ("add", "done", "delete", "edit"):
        tasks_data = load_tasks()
        history = load_undo()
        history.append(copy.deepcopy(tasks_data))
        save_undo(history)

        COMMANDS[command](tasks_data, positional, flags)
    elif command == "undo":
        tasks_data = load_tasks()
        cmd_undo(tasks_data, positional, flags)
    else:
        tasks_data = load_tasks()
        COMMANDS[command](tasks_data, positional, flags)


if __name__ == "__main__":
    main()
