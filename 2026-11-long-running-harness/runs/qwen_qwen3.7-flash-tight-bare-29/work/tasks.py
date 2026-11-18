#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


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
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(tasks, next_id):
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_undo_history(history)


def pop_undo():
    history = load_undo_history()
    if not history:
        return None
    state = history.pop()
    save_undo_history(history)
    return state["tasks"], state["next_id"]


def task_line(task):
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
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


def validate_date(value):
    try:
        parts = value.split("-")
        if len(parts) != 3:
            return False
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
        return True
    except (ValueError, TypeError):
        return False


def cmd_add(args):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due = args[i + 1]
            if not validate_date(due):
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)

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
    print(f"Added {next_id}")


def cmd_list(args):
    tasks, next_id = load_tasks()

    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    filtered = list(tasks)

    if tag_filter is not None:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    if overdue:
        if today_str:
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                error(f"Invalid date: {today_str}")
        else:
            today = date.today()
        filtered = [t for t in filtered
                    if not t["done"]
                    and t.get("due")
                    and date.fromisoformat(t["due"]) < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(task_line(task))


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)

    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)

    found = False
    new_tasks = []
    for task in tasks:
        if task["id"] == task_id:
            found = True
        else:
            new_tasks.append(task)

    if not found:
        error(f"No such task: {task_id}")

    save_tasks(new_tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")

    # Parse arguments to get ID and new title
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            title_parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            continue
        i += 1

    if new_title is None:
        error("--title flag is required")

    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)

    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")

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
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Usage: export --format json|csv")

    tasks, next_id = load_tasks()
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
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{str(task['done']).lower()},{task.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    tasks, next_id = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    result = pop_undo()
    if result is None:
        error("Nothing to undo")
    tasks, next_id = result
    save_tasks(tasks, next_id)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
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

    if command not in commands:
        error(f"Unknown command: {command}")

    commands[command](args)


if __name__ == "__main__":
    main()
