#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task_line(task):
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{tid} {status} {task['title']}"]
    pri = task.get("priority", "medium")
    if pri == "high":
        parts.append("(high)")
    elif pri == "low":
        parts.append("(low)")
    tags = task.get("tags", [])
    if tags:
        parts.extend(tags)
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def find_task(data, task_id):
    return data["tasks"].get(task_id)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def push_undo(data):
    data["history"].append({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    })


def cmd_add(args, data):
    priority = "medium"
    tags = []
    due = None
    i = 0
    positional = []
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value after --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value after --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value after --due")
            due_val = args[i + 1]
            try:
                datetime.strptime(due_val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_val}")
            due = due_val
            i += 2
        else:
            positional.append(args[i])
            i += 1
    if not positional:
        error("Missing task title")
    title = " ".join(positional)
    push_undo(data)
    task_id = data["next_id"]
    data["next_id"] += 1
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_priority = args[i + 1] == "priority"
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
    tasks = list(data["tasks"].values())
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        if today_str is None:
            today_val = date.today().isoformat()
        else:
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today_str}")
            today_val = today_str
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_val]
    if sort_priority:
        pri_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (pri_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(format_task_line(t))


def cmd_done(args, data):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    task = find_task(data, task_id)
    if task is None:
        error(f"No such task: {task_id}")
    push_undo(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    task = find_task(data, task_id)
    if task is None:
        error(f"No such task: {task_id}")
    push_undo(data)
    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    task = find_task(data, task_id)
    if task is None:
        error(f"No such task: {task_id}")
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing value after --title")
            new_title = " ".join(args[i + 1:])
            break
        i += 1
    if new_title is None:
        error("Missing --title for edit")
    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task_line(t))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            lines.append(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')
        print("\n".join(lines))


def cmd_stats(args, data):
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if not data["history"]:
        error("Nothing to undo")
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
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
    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    data = load_data()
    COMMANDS[command](sys.argv[2:], data)


if __name__ == "__main__":
    main()
