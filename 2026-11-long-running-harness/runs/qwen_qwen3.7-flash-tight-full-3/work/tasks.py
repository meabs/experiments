#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import json
import os
import sys
from datetime import datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def push_undo(tasks, next_id):
    history = load_undo()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_undo(history)


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    tasks = load_tasks()
    next_id = get_next_id(tasks)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    push_undo(tasks, next_id)
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks = load_tasks()
    sort_priority = False
    filter_tag = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif arg == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1
    if overdue:
        if today is None:
            today = datetime.now().strftime("%Y-%m-%d")
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due") and t["due"] < today:
                filtered.append(t)
        tasks = filtered
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(format_task(t))


def cmd_done(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t["id"] == task_id:
            if not t["done"]:
                push_undo(tasks, get_next_id(tasks))
            t["done"] = True
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    new_tasks = []
    found = False
    for t in tasks:
        if t["id"] == task_id:
            found = True
            continue
        new_tasks.append(t)
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, get_next_id(tasks))
    save_tasks(new_tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            i += 1
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            continue
        i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t["id"] == task_id:
            if t["title"] != new_title:
                push_undo(tasks, get_next_id(tasks))
            t["title"] = new_title
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not fmt:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in tasks:
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
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_undo()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = history.pop()
    save_undo(history)
    save_tasks(state["tasks"])
    # The next_id is restored by the saved tasks list since we store the full
    # tasks list including the deleted one that caused the gap in IDs.
    # We don't need to do anything special - the tasks list itself is enough.
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
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
