#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1}


def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def append_undo(prev_data):
    history = load_undo()
    history.append(prev_data)
    save_undo(history)


def parse_add_args(args):
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    title = " ".join(title_parts)
    if not title:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    return title, priority, tags, due


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    data = load_tasks()
    title, priority, tags, due = parse_add_args(args)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    prev_data = json.loads(json.dumps(data))
    append_undo(prev_data)
    data["tasks"].append(task)
    data["next_id"] += 1
    save_tasks(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_tasks()
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return

    # Parse filters
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing today value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    filtered = list(tasks)

    if filter_tag:
        filtered = [t for t in filtered if filter_tag in t.get("tags", [])]

    if overdue:
        if today_str is None:
            today_str = date.today().isoformat()
        # Only open tasks whose due date is before today
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    data = load_tasks()
    try:
        tid = int(args[0])
    except (ValueError, IndexError):
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    prev_data = json.loads(json.dumps(data))
    append_undo(prev_data)
    task["done"] = True
    save_tasks(data)
    print(f"Done {tid}")


def cmd_delete(args):
    data = load_tasks()
    try:
        tid = int(args[0])
    except (ValueError, IndexError):
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    prev_data = json.loads(json.dumps(data))
    append_undo(prev_data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_tasks(data)
    print(f"Deleted {tid}")


def cmd_edit(args):
    data = load_tasks()
    try:
        tid = int(args[0])
    except (ValueError, IndexError):
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
        else:
            i += 1

    new_title = " ".join(new_title_parts)
    if not new_title:
        print("Missing new title", file=sys.stderr)
        sys.exit(1)

    prev_data = json.loads(json.dumps(data))
    append_undo(prev_data)
    task["title"] = new_title
    save_tasks(data)
    print(f"Edited {tid}")


def cmd_search(args):
    data = load_tasks()
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    text = " ".join(args).lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    data = load_tasks()
    fmt = "json"
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{str(t['done']).lower()},{t['priority']},{tags_str},{due_str}")
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
    history = load_undo()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_data = history.pop()
    save_undo(history)
    save_tasks(prev_data)
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
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
