#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
import copy
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from file. Returns (tasks, next_id, history)."""
    if not os.path.exists(DATA_FILE):
        return [], 1, []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1), data.get("history", [])
    except (json.JSONDecodeError, KeyError):
        return [], 1, []


def save_data(tasks, next_id, history):
    """Save tasks data to file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id, "history": history}, f, indent=2)


def format_task(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    # Priority suffix: high and low only
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += " #{}".format(tag)
    # Due date suffix
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def parse_args(args):
    """Parse command-line arguments into options dict and positional args."""
    options = {}
    i = 0
    positional = []
    while i < len(args):
        arg = args[i]
        if arg in ("--priority", "--tag", "--due", "--title", "--sort", "--today", "--format"):
            key = arg.lstrip("-")
            if i + 1 >= len(args):
                print("Missing value for {}".format(arg), file=sys.stderr)
                sys.exit(1)
            if key == "tag":
                options.setdefault("tags", []).append(args[i + 1])
            elif key == "title":
                options["new_title"] = args[i + 1]
            else:
                options[key] = args[i + 1]
            i += 2
        elif arg == "--overdue":
            options["overdue"] = True
            i += 1
        elif arg.startswith("--"):
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)
        else:
            positional.append(arg)
            i += 1
    options["_positional"] = positional
    return options


def validate_date(value):
    """Check if a string is a valid YYYY-MM-DD date."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    """Add a new task."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(positional)
    priority = opts.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)
    tags = opts.get("tags", [])
    due = opts.get("due", None)
    if due is not None:
        if not validate_date(due):
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)
    tasks, next_id, history = load_data()
    # Save state before mutation
    history.append(copy.deepcopy({"tasks": tasks, "next_id": next_id}))
    new_task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(new_task)
    save_data(tasks, next_id + 1, history)
    print("Added {}".format(next_id))


def cmd_list(args):
    """List tasks with optional filtering and sorting."""
    opts = parse_args(args)
    tasks, next_id, history = load_data()
    if not tasks:
        print("No tasks")
        return
    filtered = list(tasks)
    # Filter by tag
    if "tag" in opts:
        tag_filter = opts["tag"]
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]
    # Filter overdue
    if opts.get("overdue"):
        today_str = opts.get("today", date.today().isoformat())
        if not validate_date(today_str):
            print("Invalid date: {}".format(today_str), file=sys.stderr)
            sys.exit(1)
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]
    # Sort by priority
    sort_opt = opts.get("sort")
    if sort_opt == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    elif sort_opt:
        print("Unknown sort option: {}".format(sort_opt), file=sys.stderr)
        sys.exit(1)
    if not filtered:
        print("No tasks")
        return
    for task in filtered:
        print(format_task(task))


def cmd_done(args):
    """Mark a task as done."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)
    tasks, next_id, history = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    # Save state before mutation
    history.append(copy.deepcopy({"tasks": tasks, "next_id": next_id}))
    found["done"] = True
    save_data(tasks, next_id, history)
    print("Done {}".format(task_id))


def cmd_delete(args):
    """Delete a task."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)
    tasks, next_id, history = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    # Save state before mutation
    history.append(copy.deepcopy({"tasks": tasks, "next_id": next_id}))
    tasks = [t for t in tasks if t["id"] != task_id]
    save_data(tasks, next_id, history)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    """Edit a task's title."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)
    if "new_title" not in opts:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    new_title = opts["new_title"]
    tasks, next_id, history = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    # Save state before mutation
    history.append(copy.deepcopy({"tasks": tasks, "next_id": next_id}))
    found["title"] = new_title
    save_data(tasks, next_id, history)
    print("Edited {}".format(task_id))


def cmd_search(args):
    """Search tasks by title (case-insensitive)."""
    opts = parse_args(args)
    positional = opts["_positional"]
    if not positional:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    text = " ".join(positional).lower()
    tasks, next_id, history = load_data()
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    opts = parse_args(args)
    fmt = opts.get("format")
    if not fmt:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)
    if fmt not in ("json", "csv"):
        print("Unknown format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)
    tasks, next_id, history = load_data()
    # Sort by id
    tasks_sorted = sorted(tasks, key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks_sorted:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks_sorted:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str
            ))


def cmd_stats(args):
    """Print task statistics."""
    tasks, next_id, history = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    """Undo the most recent mutating command."""
    tasks, next_id, history = load_data()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    # Pop the last state
    prev_state = history.pop()
    save_data(prev_state["tasks"], prev_state["next_id"], history)
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
