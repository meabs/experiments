#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_data():
    """Load tasks and next_id from tasks.json."""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], 1


def save_data(tasks, next_id):
    """Save tasks and next_id to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    """Load undo history from undo_history.json."""
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_undo_history(history):
    """Save undo history to undo_history.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def format_task(task):
    """Format a task into the display line."""
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # medium shows no suffix
    # Tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def record_undo(state):
    """Record current state for undo."""
    history = load_undo_history()
    history.append({"type": state.get("cmd_type"), "state": state})
    save_undo_history(history)


def cmd_add(args):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("--priority requires a value")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("--due requires a value")
            due = args[i]
            # Validate date
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Title is required")

    title = " ".join(title_parts)

    tasks, next_id = load_data()
    old_state = {"tasks": copy.deepcopy(tasks), "next_id": next_id}

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
    save_data(tasks, next_id)

    record_undo(old_state)

    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    tasks, _ = load_data()

    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                error("--sort requires a value")
            if args[i] == "priority":
                sort_priority = True
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag filter requires a value")
            tag_filter = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                error("--today requires a date value")
            today_str = args[i]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today_str}")
        i += 1

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    if overdue:
        today = date.today() if today_str is None else datetime.strptime(today_str, "%Y-%m-%d").date()
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t["due"]:
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        error("ID is required")
    task_id = int(args[0])

    tasks, next_id = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        error(f"No such task: {task_id}")

    old_state = {"tasks": copy.deepcopy(tasks), "next_id": next_id}
    found["done"] = True
    save_data(tasks, next_id)

    record_undo(old_state)

    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("ID is required")
    task_id = int(args[0])

    tasks, next_id = load_data()
    found_idx = None
    for idx, t in enumerate(tasks):
        if t["id"] == task_id:
            found_idx = idx
            break

    if found_idx is None:
        error(f"No such task: {task_id}")

    old_state = {"tasks": copy.deepcopy(tasks), "next_id": next_id}
    del tasks[found_idx]
    save_data(tasks, next_id)

    record_undo(old_state)

    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("ID is required")
    task_id = int(args[0])

    tasks, next_id = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1  # Skip ID
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            i += 1
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            if not parts:
                error("--title requires a value")
            new_title = " ".join(parts)
        else:
            i += 1
        i += 1

    if new_title is None:
        error("--title is required")

    old_state = {"tasks": copy.deepcopy(tasks), "next_id": next_id}
    found["title"] = new_title
    save_data(tasks, next_id)

    record_undo(old_state)

    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        error("Search text is required")
    query = " ".join(args).lower()

    tasks, _ = load_data()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            i += 1
            if i >= len(args):
                error("--format requires a value")
            fmt = args[i]
        i += 1

    if fmt is None:
        error("--format is required")

    tasks, _ = load_data()
    tasks.sort(key=lambda t: t["id"])

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
        print(json.dumps(export_data))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] or "",
            ])
        print(output.getvalue(), end="")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle 'stats' command."""
    tasks, _ = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    entry = history.pop()
    save_undo_history(history)

    state = entry["state"]
    save_data(state["tasks"], state["next_id"])

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

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
