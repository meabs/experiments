#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date

DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = '{} [{}] {}'.format(task["id"], status, task["title"])
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    for tag in task["tags"]:
        line += " #{}".format(tag)
    if task["due"]:
        line += " due:{}".format(task["due"])
    return line


def parse_add_args(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(priority))
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                parts = due.split("-")
                if len(parts) != 3:
                    raise ValueError()
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, IndexError):
                error("Invalid date: {}".format(due))
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    return title_parts, priority, tags, due


def cmd_add(args):
    if not args:
        error("Usage: tasks.py add TITLE [--priority high|medium|low] [--tag TAG...] [--due YYYY-MM-DD]")
    title_parts, priority, tags, due = parse_add_args(args)
    title = " ".join(title_parts)
    if not title:
        error("Missing title")
    tasks, next_id = load_tasks()
    task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    history = load_history()
    history.append({"action": "add", "task": task, "next_id": next_id})
    save_history(history)
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print("Added {}".format(task["id"]))


def cmd_list(args):
    tasks, next_id = load_tasks()
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    if overdue:
        if today_str:
            try:
                parts = today_str.split("-")
                today = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                error("Invalid date: {}".format(today_str))
        else:
            today = date.today()
        filtered = []
        for t in tasks:
            if t["due"] and not t["done"]:
                try:
                    parts = t["due"].split("-")
                    due_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    if due_date < today:
                        filtered.append(t)
                except (ValueError, IndexError):
                    pass
        tasks = filtered
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]
    if sort_priority:
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(format_task_line(t))


def cmd_done(args):
    if not args:
        error("Usage: tasks.py done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: {}".format(args[0]))
    tasks, next_id = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: {}".format(task_id))
    history = load_history()
    history.append({"action": "done", "task": dict(task), "next_id": next_id})
    save_history(history)
    task["done"] = True
    save_tasks(tasks, next_id)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        error("Usage: tasks.py delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: {}".format(args[0]))
    tasks, next_id = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: {}".format(task_id))
    history = load_history()
    history.append({"action": "delete", "task": dict(task), "next_id": next_id})
    save_history(history)
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks, next_id)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        error("Usage: tasks.py edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: {}".format(args[0]))
    tasks, next_id = load_tasks()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: {}".format(task_id))
    title_idx = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_idx = i
            break
    if title_idx is None or title_idx + 1 >= len(args):
        error("Missing --title value")
    new_title = " ".join(args[title_idx + 1:])
    history = load_history()
    history.append({"action": "edit", "task": dict(task), "next_id": next_id})
    save_history(history)
    task["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        error("Usage: tasks.py search TEXT")
    query = " ".join(args).lower()
    tasks, next_id = load_tasks()
    matches = sorted([t for t in tasks if query in t["title"].lower()], key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task_line(t))


def cmd_export(args):
    if not args:
        error("Usage: tasks.py export --format json|csv")
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        error("Usage: tasks.py export --format json|csv")
    tasks, next_id = load_tasks()
    tasks = sorted(tasks, key=lambda t: t["id"])
    if fmt == "json":
        export_data = [{"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"], "tags": t["tags"], "due": t["due"]} for t in tasks]
        print(json.dumps(export_data))
    else:
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print("{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t["priority"], tags_str, due_str))


def cmd_stats(args):
    tasks, next_id = load_tasks()
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
    last = history.pop()
    save_history(history)
    action = last["action"]
    if action == "add":
        task = last["task"]
        tasks, _ = load_tasks()
        tasks = [t for t in tasks if t["id"] != task["id"]]
        next_id = last["next_id"]
    elif action == "done":
        task = last["task"]
        tasks, next_id = load_tasks()
        for t in tasks:
            if t["id"] == task["id"]:
                t["done"] = False
                break
    elif action == "delete":
        task = last["task"]
        tasks, next_id = load_tasks()
        tasks.append(dict(task))
    elif action == "edit":
        task = last["task"]
        tasks, next_id = load_tasks()
        for t in tasks:
            if t["id"] == task["id"]:
                t["title"] = task["title"]
                break
    save_tasks(tasks, next_id)
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
        error("Usage: tasks.py <command> [args]")
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        error("Unknown command: {}".format(cmd))
    COMMANDS[cmd](sys.argv[2:])


if __name__ == "__main__":
    main()
