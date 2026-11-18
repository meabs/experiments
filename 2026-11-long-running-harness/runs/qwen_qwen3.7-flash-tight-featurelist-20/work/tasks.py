#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", [])


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f).get("history", [])


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump({"history": history}, f)


def record_undo(tasks, next_id):
    """Record current state for undo. Called BEFORE mutation."""
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


def format_task(task):
    status = "[x]" if task["done"] else "[ ]"
    line = '{} {} {}'.format(task["id"], status, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join("#" + t for t in task["tags"])
    if task.get("due"):
        line += " due:" + task["due"]
    return line


def validate_date(due):
    try:
        parts = due.split("-")
        if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
            raise ValueError
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        if month < 1 or month > 12:
            raise ValueError
        if day < 1 or day > 31:
            raise ValueError
        days_in_month = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if day > days_in_month[month]:
            raise ValueError
    except (ValueError, IndexError):
        error("Invalid date: " + due)


def cmd_add(args):
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: " + priority)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("Missing task title")
    title = " ".join(title_parts)
    if due is not None:
        validate_date(due)
    tasks = load_tasks()
    next_id = get_next_id(tasks)
    record_undo(tasks, next_id)
    task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    tasks.append(task)
    save_tasks(tasks)
    print("Added " + str(next_id))


def cmd_list(args):
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
    if today is None:
        import datetime
        today = datetime.date.today().isoformat()
    tasks = load_tasks()
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: " + str(task_id))
    record_undo(tasks, get_next_id(tasks))
    task["done"] = True
    save_tasks(tasks)
    print("Done " + str(task_id))


def cmd_delete(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t["id"] == task_id:
            found = True
            break
    if not found:
        error("No such task: " + str(task_id))
    new_tasks = [t for t in tasks if t["id"] != task_id]
    record_undo(tasks, get_next_id(tasks))
    save_tasks(new_tasks)
    print("Deleted " + str(task_id))


def cmd_edit(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    tasks = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: " + str(task_id))
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing new title")
            new_title = " ".join(args[i + 1:])
            break
        i += 1
    if new_title is None:
        error("Missing --title option")
    record_undo(tasks, get_next_id(tasks))
    task["title"] = new_title
    save_tasks(tasks)
    print("Edited " + str(task_id))


def cmd_search(args):
    if not args:
        error("Missing search text")
    search_text = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
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
    if fmt is None:
        error("Missing --format option")
    if fmt not in ("json", "csv"):
        error("Invalid format: " + fmt)
    tasks = load_tasks()
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
                "due": t.get("due", None)
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print("{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t.get("priority", "medium"), tags_str, due_str))


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    history = load_history()
    if not history:
        error("Nothing to undo")
    state = history.pop()
    save_history(history)
    save_tasks(state["tasks"])
    # Restore next_id by using the saved one
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
    if command not in COMMANDS:
        error("Unknown command: " + command)
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
