#!/usr/bin/env python3
"""A command-line task manager using only Python 3 standard library."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(data):
    history = load_history()
    history.append(json.loads(json.dumps(data)))
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_data = history.pop()
    save_history(history)
    return prev_data


def is_valid_date(date_str):
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return False
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        datetime(year, month, day)
        return True
    except (ValueError, TypeError):
        return False


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}' 
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

def cmd_add(args):
    data = load_data()
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Invalid date: ", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            if not is_valid_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1
    if title is None or title.strip() == "":
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    push_history(data)
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"])
    sort_by = None
    tag_filter = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            if sort_by not in ("priority",):
                print(f"--sort only supports 'priority'", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Invalid date: ", file=sys.stderr)
                sys.exit(1)
            today_arg = args[i + 1]
            if not is_valid_date(today_arg):
                print(f"Invalid date: {today_arg}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today_arg:
            today_str = today_arg
        else:
            today_str = date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    data = load_data()
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            push_history(data)
            save_data(data)
            print(f"Done {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    data = load_data()
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"].pop(i)
            push_history(data)
            save_data(data)
            print(f"Deleted {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    data = load_data()
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            # Collect all consecutive non-flag arguments as the title
            i += 1
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1
    if new_title is None or new_title.strip() == "":
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["title"] = new_title
            push_history(data)
            save_data(data)
            print(f"Edited {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    data = load_data()
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"], key=lambda t: t["id"]):
        if text in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires json or csv", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Unsupported format: {fmt}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for task in tasks:
            result.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due", None),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{str(task['done']).lower()},{task.get('priority','medium')},{tags_str},{due_str}")


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(args):
    prev_data = pop_history()
    save_data(prev_data)
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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
