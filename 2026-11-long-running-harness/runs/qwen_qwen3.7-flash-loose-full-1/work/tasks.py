#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
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
    history.append(json.dumps(data))
    if len(history) > 100:
        history = history[-100:]
    save_undo_history(history)


def cmd_undo(args):
    history = load_undo_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = history.pop()
    save_undo_history(history)
    saved_data = json.loads(prev_state)
    save_data(saved_data)
    print("Undone")


def parse_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        print(f"Invalid date: {value}", file=sys.stderr)
        sys.exit(1)


def validate_priority(value):
    valid = ("high", "medium", "low")
    if value not in valid:
        print(f"Invalid priority: {value}", file=sys.stderr)
        sys.exit(1)
    return value


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args):
    data = load_data()
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = validate_priority(args[i + 1])
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
            due = parse_date(args[i + 1])
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    title = " ".join(title_parts)
    if not title:
        print("Title is required", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return
    sort_by = None
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
            sort_by = args[i + 1]
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
    filtered = list(tasks)
    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]
    if overdue:
        today = date.today() if today_str is None else date.fromisoformat(today_str)
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due")
            and date.fromisoformat(t["due"]) < today
        ]
    if sort_by == "priority":
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
        print("ID is required", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("ID is required", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        print("ID is required", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title_parts = args[i + 1:]
            new_title = " ".join(new_title_parts)
            break
        i += 1
    if new_title is None:
        print("--title is required", file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Search text is required", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()
    data = load_data()
    matches = []
    for t in data["tasks"]:
        if search_text in t["title"].lower():
            matches.append(t)
    if not matches:
        print("No matches")
        return
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(task_line(task))


def cmd_export(args):
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
    if fmt is None:
        print("--format is required", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
