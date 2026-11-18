#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_data():
    """Load tasks and next_id from the data file."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        next_id = data.get("next_id", max((t["id"] for t in tasks), default=0) + 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id=None):
    """Save tasks and optionally next_id to the data file."""
    if next_id is None:
        _, next_id = load_data()
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f, indent=2)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def push_undo(tasks, next_id):
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_undo_history(history)


def cmd_add(args):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due_str = args[i + 1]
            try:
                parts = due_str.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                datetime(y, m, d)
                due = due_str
            except (ValueError, IndexError):
                error(f"Invalid date: {due_str}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("add requires a TITLE")
    title = " ".join(title_parts)
    tasks, next_id = load_data()
    # Push OLD state before mutation
    push_undo(tasks, next_id)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    sort_option = None
    tag_filter = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_option = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1
    tasks, _ = load_data()
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        today_str = today_arg if today_arg else date.today().isoformat()
        try:
            today_date = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    tasks, next_id = load_data()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    # Push OLD state before mutation
    push_undo(tasks, next_id)
    task["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    tasks, next_id = load_data()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    # Push OLD state before mutation
    push_undo(tasks, next_id)
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    title_start = None
    for idx, arg in enumerate(args[1:], 1):
        if arg == "--title":
            title_start = idx + 1
            break
    if title_start is None or title_start >= len(args):
        error("edit requires --title NEW TITLE")
    new_title = " ".join(args[title_start:])
    tasks, next_id = load_data()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    # Push OLD state before mutation
    push_undo(tasks, next_id)
    task["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args).lower()
    tasks, _ = load_data()
    matches = [t for t in tasks if text in t["title"].lower()]
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
    if fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")
    tasks, _ = load_data()
    tasks.sort(key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            pid = t["id"]
            tit = t["title"]
            pri = t.get("priority", "medium")
            print(f"{pid},{tit},{done_str},{pri},{tags_str},{due_str}")


def cmd_stats(args):
    tasks, _ = load_data()
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
    save_tasks(state["tasks"], state["next_id"])
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
