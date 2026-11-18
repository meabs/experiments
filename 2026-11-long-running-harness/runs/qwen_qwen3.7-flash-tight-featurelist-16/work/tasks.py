#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks.undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_undo(data):
    history = load_undo_history()
    history.append(json.loads(json.dumps(data)))
    save_undo_history(history)


def format_task_line(task):
    line = "{} [{}] {}".format(task["id"], "x" if task["done"] else " ", task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    for tag in task.get("tags", []):
        line += " #{}".format(tag)
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def cmd_add(args, data):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(due), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg.startswith("--"):
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        print("add requires a title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    next_id = data["next_id"]
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][str(next_id)] = task
    data["next_id"] = next_id + 1
    push_undo(data)
    save_tasks(data)
    print("Added {}".format(next_id))


def cmd_list(args, data):
    sort_by = None
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]
            i += 2
        elif arg == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(format_task_line(task))


def cmd_done(args, data):
    if not args:
        print("done requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    key = str(task_id)
    if key not in data["tasks"]:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    data["tasks"][key]["done"] = True
    push_undo(data)
    save_tasks(data)
    print("Done {}".format(task_id))


def cmd_delete(args, data):
    if not args:
        print("delete requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    key = str(task_id)
    if key not in data["tasks"]:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    del data["tasks"][key]
    push_undo(data)
    save_tasks(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args, data):
    task_id = None
    new_title = None
    i = 0
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            if task_id is None:
                print("--title must come after the ID", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(args[i + 1:])
            break
        elif task_id is None:
            try:
                task_id = int(args[i])
            except ValueError:
                print("No such task: {}".format(args[i]), file=sys.stderr)
                sys.exit(1)
        i += 1
    if task_id is None or new_title is None:
        print("edit requires ID and --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    key = str(task_id)
    if key not in data["tasks"]:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    data["tasks"][key]["title"] = new_title
    push_undo(data)
    save_tasks(data)
    print("Edited {}".format(task_id))


def cmd_search(args, data):
    if not args:
        print("search requires TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not fmt:
        print("export requires --format json|csv", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
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
            due_str = task.get("due", "")
            print("{},{},{},{},{},{}".format(task["id"], task["title"], done_str, task.get("priority", "medium"), tags_str, due_str))
    else:
        print("Unknown format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    data = load_tasks()
    if command == "add":
        cmd_add(args, data)
    elif command == "list":
        cmd_list(args, data)
    elif command == "done":
        cmd_done(args, data)
    elif command == "delete":
        cmd_delete(args, data)
    elif command == "edit":
        cmd_edit(args, data)
    elif command == "search":
        cmd_search(args, data)
    elif command == "export":
        cmd_export(args, data)
    elif command == "stats":
        cmd_stats(args, data)
    elif command == "undo":
        undo()
    else:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
