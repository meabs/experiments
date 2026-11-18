#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def format_task(task):
    status = "[x]" if task["done"] else "[ ]"
    line = '{} {} {}'.format(task["id"], status, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    if task.get("due"):
        line += ' due:{}'.format(task["due"])
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(priority))
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: {}".format(due))
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    title = " ".join(title_parts)
    if not title:
        error("Title cannot be empty")
    tasks, next_id = load_tasks()
    # Save snapshot BEFORE adding
    tasks_before = [dict(t) for t in tasks]
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
    history = load_undo()
    history.append({
        "action": "add",
        "tasks_snapshot": tasks_before,
        "next_id": next_id,
    })
    save_undo(history)
    print("Added {}".format(new_task["id"]))


def cmd_list(args):
    sort_priority = False
    filter_tag = None
    show_overdue = False
    today_date = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]
            if sort_by == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            show_overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_date = args[i + 1]
            i += 2
        else:
            i += 1
    tasks, _ = load_tasks()
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if show_overdue:
        if today_date:
            try:
                today = datetime.strptime(today_date, "%Y-%m-%d").date()
            except ValueError:
                error("Invalid date: {}".format(today_date))
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and datetime.strptime(t["due"], "%Y-%m-%d").date() < today]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: {}".format(args[0]))
    tasks, next_id = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            # Save snapshot BEFORE marking done
            tasks_before = [dict(t) for t in tasks]
            task["done"] = True
            found = True
            break
    if not found:
        error("No such task: {}".format(task_id))
    save_tasks(tasks, next_id)
    history = load_undo()
    history.append({
        "action": "done",
        "tasks_snapshot": tasks_before,
        "next_id": next_id,
    })
    save_undo(history)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: {}".format(args[0]))
    tasks, next_id = load_tasks()
    found = False
    deleted_task = None
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            # Save snapshot BEFORE deletion
            tasks_before = [dict(t) for t in tasks]
            deleted_task = dict(task)
            tasks.pop(i)
            found = True
            break
    if not found:
        error("No such task: {}".format(task_id))
    save_tasks(tasks, next_id)
    history = load_undo()
    history.append({
        "action": "delete",
        "task_id": task_id,
        "deleted_task": deleted_task,
        "tasks_snapshot": tasks_before,
        "next_id": next_id,
    })
    save_undo(history)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: {}".format(args[0]))
    title_idx = None
    for i, arg in enumerate(args[1:], 1):
        if arg == "--title":
            title_idx = i
            break
    if title_idx is None:
        error("Usage: edit ID --title NEW TITLE")
    if title_idx + 1 >= len(args):
        error("--title requires a value")
    new_title = " ".join(args[title_idx + 1:])
    tasks, next_id = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            # Save snapshot BEFORE editing
            tasks_before = [dict(t) for t in tasks]
            task["title"] = new_title
            found = True
            break
    if not found:
        error("No such task: {}".format(task_id))
    save_tasks(tasks, next_id)
    history = load_undo()
    history.append({
        "action": "edit",
        "task_id": task_id,
        "tasks_snapshot": tasks_before,
        "next_id": next_id,
    })
    save_undo(history)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


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
    tasks, _ = load_tasks()
    if fmt == "json":
        result = []
        for task in tasks:
            result.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print("{},{},{},{},{},{}".format(task["id"], task["title"], done_str, task.get("priority", "medium"), tags_str, due_str))


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    history = load_undo()
    if not history:
        error("Nothing to undo")
    entry = history.pop()
    save_undo(history)
    action = entry["action"]
    if action in ("add", "done", "delete", "edit"):
        tasks = entry["tasks_snapshot"]
        next_id = entry["next_id"]
        save_tasks(tasks, next_id)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: tasks.py <command> [args]")
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
        error("Unknown command: {}".format(command))
    commands[command](args)


if __name__ == "__main__":
    main()
