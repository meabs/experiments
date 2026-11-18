#!/usr/bin/env python3
"""A command-line task manager using only Python 3 standard library."""

import json
import sys
import os
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return [], 1, []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1), data.get("undo_stack", [])
    except (json.JSONDecodeError, KeyError):
        return [], 1, []


def save_data(tasks, next_id, undo_stack):
    data = {"tasks": tasks, "next_id": next_id, "undo_stack": undo_stack}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
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


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
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
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Invalid date: ")
            val = args[i + 1]
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {val}")
            due = val
            i += 2
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        error("Missing title")
    title = " ".join(title_parts)
    tasks, next_id, undo_stack = load_data()
    new_task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    tasks.append(new_task)
    undo_stack.append({"type": "add", "task_id": next_id})
    save_data(tasks, next_id + 1, undo_stack)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks, next_id, undo_stack = load_data()
    show_tag = None
    sort_by = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            show_tag = args[i + 1]
            i += 2
        elif arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_by = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a date")
            today_str = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")
    if today_str:
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
    else:
        today = date.today()
    if show_tag:
        tasks = [t for t in tasks if show_tag in t.get("tags", [])]
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    tasks, next_id, undo_stack = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        error(f"No such task: {task_id}")
    undo_stack.append({"type": "done", "task_id": task_id, "was_done": found["done"]})
    found["done"] = True
    save_data(tasks, next_id, undo_stack)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    tasks, next_id, undo_stack = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        error(f"No such task: {task_id}")
    undo_stack.append({"type": "delete", "task_id": task_id, "task": found})
    tasks = [t for t in tasks if t["id"] != task_id]
    save_data(tasks, next_id, undo_stack)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        error("Missing task id")
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
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        else:
            error(f"Unknown option: {args[i]}")
    if new_title is None:
        error("--title is required")
    tasks, next_id, undo_stack = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        error(f"No such task: {task_id}")
    undo_stack.append({"type": "edit", "task_id": task_id, "old_title": found["title"]})
    found["title"] = new_title
    save_data(tasks, next_id, undo_stack)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        error("Missing search text")
    search_text = " ".join(args).lower()
    tasks, next_id, undo_stack = load_data()
    matches = [t for t in tasks if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if fmt is None:
        error("--format is required")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    tasks, next_id, undo_stack = load_data()
    tasks = sorted(tasks, key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({"id": t["id"], "title": t["title"], "done": t["done"], "priority": t.get("priority", "medium"), "tags": t.get("tags", []), "due": t.get("due")})
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t["due"] if t.get("due") else ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    tasks, next_id, undo_stack = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    tasks, next_id, undo_stack = load_data()
    if not undo_stack:
        error("Nothing to undo")
    action = undo_stack.pop()
    atype = action["type"]
    if atype == "add":
        task_id = action["task_id"]
        tasks = [t for t in tasks if t["id"] != task_id]
        next_id = task_id
    elif atype == "done":
        task_id = action["task_id"]
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = action["was_done"]
                break
    elif atype == "delete":
        task_id = action["task_id"]
        tasks.append(action["task"])
    elif atype == "edit":
        task_id = action["task_id"]
        for t in tasks:
            if t["id"] == task_id:
                t["title"] = action["old_title"]
                break
    save_data(tasks, next_id, undo_stack)
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
