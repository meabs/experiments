#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = ".undo_history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    suffix = ""
    if task.get("priority") == "high":
        suffix += " (high)"
    elif task.get("priority") == "low":
        suffix += " (low)"
    for tag in task.get("tags", []):
        suffix += f" #{tag}"
    if task.get("due"):
        suffix += f" due:{task['due']}"
    return line + suffix


def record_undo(data):
    history = load_history()
    history.append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_history(history)


def cmd_add(args, data):
    priority = "medium"
    tags = []
    due = None
    i = 0
    title_parts = []
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                return 1
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                return 1
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                return 1
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                return 1
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
                due = due_str
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                return 1
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        return 1
    title = " ".join(title_parts)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    record_undo(data)
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")
    return 0


def cmd_list(args, data):
    sort_option = None
    filter_tag = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                return 1
            sort_option = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                return 1
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
                return 1
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1
    tasks = data["tasks"]
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        today_str = today_arg if today_arg else date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return 0
    for task in tasks:
        print(format_task_line(task))
    return 0


def cmd_done(args, data):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        return 1
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        return 1
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1
    record_undo(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")
    return 0


def cmd_delete(args, data):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        return 1
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        return 1
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1
    record_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")
    return 0


def cmd_edit(args, data):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        return 1
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        return 1
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            while i < len(args) and args[i] != "--title":
                new_title_parts.append(args[i])
                i += 1
        else:
            i += 1
    if not new_title_parts:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        return 1
    new_title = " ".join(new_title_parts)
    record_undo(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")
    return 0


def cmd_search(args, data):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        return 1
    query = " ".join(args).lower()
    matches = []
    for t in data["tasks"]:
        if query in t["title"].lower():
            matches.append(t)
    if not matches:
        print("No matches")
        return 0
    for task in matches:
        print(format_task_line(task))
    return 0


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                return 1
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        return 1
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
                "due": t.get("due"),
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        return 1
    return 0


def cmd_stats(args, data):
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")
    return 0


def cmd_undo(args, data):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        return 1
    prev_state = json.loads(history.pop())
    save_history(history)
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")
    return 0


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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    exit_code = COMMANDS[command](sys.argv[2:], data)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
