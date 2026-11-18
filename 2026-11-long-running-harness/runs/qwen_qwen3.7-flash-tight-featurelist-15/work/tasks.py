#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = ".tasks_undo.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "next_id": 1}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(data):
    """Save current data state onto undo stack."""
    history = load_undo_history()
    history.append(json.loads(json.dumps(data)))
    if len(history) > 100:
        history = history[-100:]
    save_undo_history(history)


def parse_date(date_str):
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return None
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        d = date(year, month, day)
        return d.isoformat()
    except (ValueError, TypeError):
        return None


def format_task_line(task):
    done_marker = "[x]" if task["done"] else "[ ]"
    line = str(task["id"]) + " " + done_marker + " " + task["title"]
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#" + t for t in tags)
    if task.get("due"):
        line += " due:" + task["due"]
    return line


def cmd_add(args):
    if not args:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)
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
            if due is None:
                print(f"Invalid date: {args[i+1]}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    title = " ".join(title_parts)
    if not title:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    push_undo(data)
    task_id = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    sort_mode = None
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
            sort_mode = args[i + 1]
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
    if today_str is None:
        today = date.today().isoformat()
    else:
        today = today_str
    data = load_data()
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    if not tasks:
        print("No tasks")
        return
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    push_undo(data)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            save_data(data)
            print(f"Done {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    push_undo(data)
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"].pop(i)
            save_data(data)
            print(f"Deleted {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid id: {args[0]}", file=sys.stderr)
        sys.exit(1)
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title_parts.append(args[i + 1])
            i += 2
        else:
            i += 1
    new_title = " ".join(new_title_parts)
    if not new_title:
        print("--title requires a value", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    push_undo(data)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["title"] = new_title
            save_data(data)
            print(f"Edited {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    data = load_data()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


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
    if fmt not in ("json", "csv"):
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f'{t["id"]},{t["title"]},{"true" if t["done"] else "false"},{t.get("priority","medium")},{tags_str},{due_str}')


def cmd_stats(args):
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_undo_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_undo_history(history)
    # Restore tasks but keep next_id from previous state
    data = previous
    # Also need to restore next_id
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
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
