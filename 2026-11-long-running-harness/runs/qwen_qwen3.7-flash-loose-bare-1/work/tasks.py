#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
import copy
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")
    tags = task.get("tags", [])
    if tags:
        parts.extend("#" + t for t in tags)
    if task.get("due"):
        parts.append("due:" + task["due"])
    return " ".join(parts)


def get_task(data, task_id):
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")
    return data["tasks"][key]


def cmd_add(args, data):
    title_parts = []
    priority = None
    tags = []
    due = None
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
            due_val = args[i + 1]
            if not validate_date(due_val):
                error(f"Invalid date: {due_val}")
            due = due_val
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["next_id"] += 1

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }

    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"] - 1}))
    data["tasks"][str(task_id)] = task

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date value")
            today_str = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    tasks = list(data["tasks"].values())

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    if not tasks:
        print("No tasks")
        return

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    get_task(data, task_id)

    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    data["tasks"][str(task_id)]["done"] = True

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    get_task(data, task_id)

    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    del data["tasks"][str(task_id)]

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    get_task(data, task_id)

    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
            break
        else:
            i += 1

    if not new_title_parts:
        error("--title requires a value")

    new_title = " ".join(new_title_parts)

    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    data["tasks"][str(task_id)]["title"] = new_title

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    results = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            results.append(task)

    if not results:
        print("No matches")
        return

    for task in results:
        print(task_line(task))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                error(f"Unknown format: {fmt}")
            i += 2
        else:
            error(f"Unknown option: {args[i]}")

    if not fmt:
        error("--format is required")

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
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](sys.argv[2:], data)
    save_data(data)


if __name__ == "__main__":
    main()
