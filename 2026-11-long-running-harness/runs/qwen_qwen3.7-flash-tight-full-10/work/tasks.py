#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        next_id = data.get("next_id", 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_history(history)


def undo():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_history(history)
    save_tasks(previous["tasks"], previous["next_id"])
    print("Undone")


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = '{} {} {}'.format(task["id"], status, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        tag_str = " ".join("#{}".format(t) for t in tags)
        line += " {}".format(tag_str)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def parse_date(value):
    """Parse and validate a YYYY-MM-DD date string. Returns the string or None."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


def cmd_add(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(val), file=sys.stderr)
                sys.exit(1)
            priority = val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date", file=sys.stderr)
                sys.exit(1)
            val = args[i + 1]
            parsed = parse_date(val)
            if parsed is None:
                print("Invalid date: {}".format(val), file=sys.stderr)
                sys.exit(1)
            due = parsed
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    new_task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(new_task)
    save_tasks(tasks, next_id + 1)
    push_history(tasks, next_id + 1)
    print("Added {}".format(next_id))


def cmd_list(args):
    sort_priority = False
    filter_tag = None
    show_overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            show_overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    tasks, _ = load_tasks()

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if show_overdue:
        if today_str:
            today = parse_date(today_str)
        else:
            today = date.today().isoformat()
        if today is not None:
            tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    save_tasks(tasks, next_id)
    push_history(tasks, next_id)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    new_tasks = []
    for task in tasks:
        if task["id"] == task_id:
            found = True
        else:
            new_tasks.append(task)
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    save_tasks(new_tasks, next_id)
    push_history(tasks, next_id)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    save_tasks(tasks, next_id)
    push_history(tasks, next_id)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    tasks, _ = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()
    tasks.sort(key=lambda t: t["id"])

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
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print("{},{},{},{},{},{}".format(
                task["id"], task["title"], done_str,
                task.get("priority", "medium"), tags_str, due_str))
    else:
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": lambda a: undo(),
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
