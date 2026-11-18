#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(state):
    """Save current state before a mutation so it can be undone later."""
    history = load_history()
    history.append(state)
    save_history(history)


def undo():
    """Undo the most recent mutation by restoring the previous state."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    # Pop the snapshot we want to restore (it was saved *before* the last mutation)
    prev_state = history.pop()
    save_history(history)
    # Save the current state (before undo) into history so future undos work
    current = load_tasks()
    history.append(current)
    save_history(history)
    # Restore previous state
    save_tasks(prev_state)
    print("Undone")


def format_task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    # Add priority suffix (only high/low shown)
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    # medium shows no suffix
    # Add tags suffix
    for tag in task.get("tags", []):
        line += " #{}".format(tag)
    # Add due date suffix
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def cmd_add(args):
    data = load_tasks()
    priority = "medium"
    tags = []
    due = None

    i = 0
    title_parts = []
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            i += 2
            continue
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
            continue
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Invalid date: ", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(due_str), file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
            continue
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("No title provided", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)

    # Save state BEFORE mutation for undo
    push_history(data)

    task_id = data["next_id"]
    data["tasks"][str(task_id)] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = task_id + 1
    save_tasks(data)
    print("Added {}".format(task_id))


def cmd_list(args):
    data = load_tasks()
    tasks = list(data["tasks"].values())

    sort_mode = None
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
            continue
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
            continue
        elif args[i] == "--overdue":
            overdue = True
            i += 1
            continue
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
            continue
        else:
            i += 1

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue:
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    # default sort is by id

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    data = load_tasks()
    task_id = int(args[0])
    key = str(task_id)
    if key not in data["tasks"]:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    # Save state BEFORE mutation for undo
    push_history(data)

    data["tasks"][key]["done"] = True
    save_tasks(data)
    print("Done {}".format(task_id))


def cmd_delete(args):
    data = load_tasks()
    task_id = int(args[0])
    key = str(task_id)
    if key not in data["tasks"]:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    # Save state BEFORE mutation for undo
    push_history(data)

    del data["tasks"][key]
    save_tasks(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    data = load_tasks()
    task_id = int(args[0])
    key = str(task_id)
    if key not in data["tasks"]:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    # Parse --title from remaining args
    new_title = None
    i = 1
    title_parts = []
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            i += 1
            title_parts = []
            while i < len(args):
                if args[i].startswith("--"):
                    break
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            continue
        i += 1

    if new_title is None or new_title == "":
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    # Save state BEFORE mutation for undo
    push_history(data)

    data["tasks"][key]["title"] = new_title
    save_tasks(data)
    print("Edited {}".format(task_id))


def cmd_search(args):
    data = load_tasks()
    if not args:
        print("No search text provided", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    data = load_tasks()
    fmt = None

    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
            continue
        i += 1

    if fmt is None:
        print("Missing --format argument", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

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
        print(json.dumps(export_data))
    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            lines.append("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str
            ))
        print("\n".join(lines))
    else:
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_tasks()
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "undo":
        undo()
    elif command in COMMANDS:
        COMMANDS[command](args)
    else:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
