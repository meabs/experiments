#!/usr/bin/env python3
"""A command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1}


def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def append_history(task_data):
    """Append a snapshot of task_data to the undo history."""
    history = load_history()
    history.append(json.dumps(task_data))
    save_history(history)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_date(value):
    try:
        d = datetime.strptime(value, "%Y-%m-%d").date()
        return d.isoformat()
    except ValueError:
        print(f"Invalid date: {value}", file=sys.stderr)
        sys.exit(1)


def find_task(data, task_id):
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            return i, t
    return None, None


def cmd_add(args):
    title = None
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
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                print(f"Invalid priority: {val}", file=sys.stderr)
                sys.exit(1)
            priority = val
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
            if title is not None:
                title += " " + arg
            else:
                title = arg
            i += 1
    if title is None:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    data = load_tasks()
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
    append_history(data)
    save_tasks(data)
    print(f"Added {task['id']}")


def cmd_list(args):
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
    data = load_tasks()
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today.isoformat()]
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args):
    if len(args) != 1:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    data = load_tasks()
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["done"] = True
    append_history(data)
    save_tasks(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if len(args) != 1:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    data = load_tasks()
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["tasks"].pop(idx)
    append_history(data)
    save_tasks(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if len(args) < 2:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    new_title = None
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
        else:
            i += 1
    if new_title is None:
        print("--title required", file=sys.stderr)
        sys.exit(1)
    data = load_tasks()
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["title"] = new_title
    append_history(data)
    save_tasks(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if len(args) != 1:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = args[0].lower()
    data = load_tasks()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt is None:
        print("--format required", file=sys.stderr)
        sys.exit(1)
    data = load_tasks()
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
        print(json.dumps(export_data))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_tasks()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    history.pop()
    save_history(history)
    if history:
        prev_state = json.loads(history[-1])
    else:
        prev_state = {"tasks": [], "next_id": 1}
    save_tasks(prev_state)
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
