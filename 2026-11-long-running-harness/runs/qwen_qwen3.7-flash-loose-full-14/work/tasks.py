#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    for tag in task["tags"]:
        parts.append("#" + tag)
    if task["due"]:
        parts.append("due:" + task["due"])
    return " ".join(parts)


def cmd_add(args):
    data = load_data()
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
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
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    title = " ".join(title_parts)
    if not title:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)
    data["history"].append({"type": "add", "state": json.loads(json.dumps(data))})
    task = {"id": data["next_id"], "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    sort_option = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_option = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]
    if overdue:
        if today_str:
            today_iso = today_str
        else:
            today_iso = date.today().strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_iso]
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(args):
    data = load_data()
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["history"].append({"type": "done", "state": json.loads(json.dumps(data)), "task_id": task_id})
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    data = load_data()
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["history"].append({"type": "delete", "state": json.loads(json.dumps(data)), "task_id": task_id})
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    data = load_data()
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title_parts.append(args[i])
            i += 1
        else:
            i += 1
    if not new_title_parts:
        print("Error: edit --title requires a new title", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(new_title_parts)
    data["history"].append({"type": "edit", "state": json.loads(json.dumps(data)), "task_id": task_id})
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    data = load_data()
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    matches = []
    for t in data["tasks"]:
        if text in t["title"].lower():
            matches.append(t)
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def cmd_export(args):
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"], "tags": t["tags"], "due": t["due"]})
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f'{t["id"]},{t["title"]},{done_str},{t["priority"]},{tags_str},{due_str}')


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    last_action = data["history"].pop()
    prev_state = last_action["state"]
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
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
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    commands[command](args)


if __name__ == "__main__":
    main()
