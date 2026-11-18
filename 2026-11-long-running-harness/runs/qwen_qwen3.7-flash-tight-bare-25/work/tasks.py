#!/usr/bin/env python3
"""Command-line task manager."""

import sys
import json
import os
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = data.get("tasks", [])
    next_id = data.get("next_id", 1)
    return tasks, next_id


def save_tasks(tasks, next_id):
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def snapshot():
    """Save current state as an undo snapshot."""
    tasks, next_id = load_tasks()
    return {"tasks": tasks, "next_id": next_id}


def push_undo(state):
    """Push a snapshot onto the undo history."""
    history = load_undo_history()
    history.append(state)
    save_undo_history(history)


def pop_undo():
    """Pop the last snapshot and restore it."""
    history = load_undo_history()
    if not history:
        err("Nothing to undo")
    state = history.pop()
    save_undo_history(history)
    save_tasks(state["tasks"], state["next_id"])


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def err(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        err(f"Invalid date: {date_str}")
    return date_str


def cmd_add(args):
    if not args:
        err("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                err("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                err(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                err("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                err("--due requires a value")
            due = validate_date(args[i + 1])
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    title = " ".join(title_parts)
    if not title:
        err("Title cannot be empty")
    tasks, next_id = load_tasks()
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    # Save snapshot of state BEFORE adding (the state without this task)
    push_undo(snapshot())
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print(f"Added {task['id']}")


def cmd_list(args):
    tasks, next_id = load_tasks()
    sort_mode = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                err("--sort requires a value")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                err("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                err("--today requires a date value")
            today_str = args[i + 1]
            i += 2
        else:
            err(f"Unknown option: {args[i]}")
    if today_str is None:
        today = date.today().strftime("%Y-%m-%d")
    else:
        today = validate_date(today_str)
    filtered = list(tasks)
    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]
    if overdue:
        filtered = [t for t in filtered
                     if not t["done"] and t.get("due") and t["due"] < today]
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    elif sort_mode:
        err(f"Unknown sort mode: {sort_mode}")
    if not filtered:
        print("No tasks")
        return
    for task in filtered:
        print(task_line(task))


def cmd_done(args):
    if not args:
        err("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        err(f"Invalid task id: {args[0]}")
    tasks, next_id = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        err(f"No such task: {task_id}")
    # Snapshot before mutation
    push_undo(snapshot())
    task["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        err("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        err(f"Invalid task id: {args[0]}")
    tasks, next_id = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        err(f"No such task: {task_id}")
    # Snapshot before mutation
    push_undo(snapshot())
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        err("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        err(f"Invalid task id: {args[0]}")
    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                err("--title requires a value")
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
        else:
            i += 1
    new_title = " ".join(title_parts)
    if not new_title:
        err("Title cannot be empty")
    tasks, next_id = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        err(f"No such task: {task_id}")
    # Snapshot before mutation
    push_undo(snapshot())
    task["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        err("Usage: search TEXT")
    text = " ".join(args).lower()
    tasks, next_id = load_tasks()
    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                err("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        err("Usage: export --format json|csv")
    tasks, next_id = load_tasks()
    tasks.sort(key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{str(t["done"]).lower()},{t["priority"]},{tags_str},{due_str}')


def cmd_stats(args):
    tasks, next_id = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    pop_undo()
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
        err("Usage: tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        err(f"Unknown command: {command}")
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
