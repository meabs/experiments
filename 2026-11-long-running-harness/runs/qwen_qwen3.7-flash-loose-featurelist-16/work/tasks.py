#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def record_undo(tasks, next_id):
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_undo_history(history)


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join(f"#{tag}" for tag in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    # Parse --priority and --tag flags
    priority = "medium"
    tags = []
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires an argument")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires an argument")
            val = args[i + 1]
            try:
                date.fromisoformat(val)
            except ValueError:
                error(f"Invalid date: {val}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(title_parts)

    tasks = load_tasks()
    next_id = get_next_id(tasks)

    record_undo(tasks, next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": None,
    }
    # Check if --due was provided
    i = 0
    while i < len(args):
        if args[i] == "--due" and i + 1 < len(args):
            task["due"] = args[i + 1]
            break
        i += 1

    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks = load_tasks()
    if not tasks:
        print("No tasks")
        return

    # Parse list options
    sort_priority = False
    filter_tag = None
    overdue = False
    today = None

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
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue:
        if today is None:
            today = date.today().isoformat()
        try:
            today_date = date.fromisoformat(today)
        except ValueError:
            error(f"Invalid date: {today}")
        filtered = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today_date]
        tasks = filtered

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        error(f"No such task: {tid}")

    record_undo(tasks, get_next_id(tasks))
    task["done"] = True
    save_tasks(tasks)
    print(f"Done {tid}")


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        error(f"No such task: {tid}")

    record_undo(tasks, get_next_id(tasks))
    tasks = [t for t in tasks if t["id"] != tid]
    save_tasks(tasks)
    print(f"Deleted {tid}")


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        error(f"No such task: {tid}")

    # Find --title flag
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires an argument")
            parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            break
        i += 1

    if new_title is None:
        error("--title flag required")

    record_undo(tasks, get_next_id(tasks))
    task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {tid}")


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")

    query = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    if not args or args[0] != "--format" or len(args) < 3:
        error("Usage: export --format json|csv")

    fmt = args[1]
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

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
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    state = history.pop()
    save_undo_history(history)
    save_tasks(state["tasks"])
    # next_id is stored but we don't need to do anything special with it
    # since the tasks list itself encodes what ids exist
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
