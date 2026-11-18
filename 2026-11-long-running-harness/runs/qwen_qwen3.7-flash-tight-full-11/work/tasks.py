#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": {}, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def format_task_line(task):
    tid = task["id"]
    status = "x" if task["done"] else " "
    line = f"{tid} [{status}] {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    data = load_data()

    # Parse args: TITLE [--priority val] [--tag TAG] [--tag TAG2] [--due DATE]
    title_parts = []
    priority = None
    tags = []
    due = None

    i = 0
    first = True
    while i < len(args):
        if first:
            # First positional arg is part of title
            title_parts.append(args[i])
            i += 1
            first = False
        elif args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
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
            due = args[i + 1]
            # Validate date
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        error("add requires a title")

    next_id = data["next_id"]

    # Save history before mutation
    data["history"].append({
        "type": "add",
        "prev_next_id": next_id,
        "prev_tasks": dict(data["tasks"]),
    })

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"][next_id] = task
    data["next_id"] = next_id + 1

    save_data(data)
    print(f"Added {next_id}")


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"].values())

    if not tasks:
        print("No tasks")
        return

    # Filter by tag
    tag_filter = None
    sort_mode = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
            # Check for --today
            if i < len(args) and args[i] == "--today":
                if i + 1 >= len(args):
                    error("--today requires a date")
                today_str = args[i + 1]
                try:
                    datetime.strptime(today_str, "%Y-%m-%d")
                except ValueError:
                    error(f"Invalid date: {today_str}")
                i += 2
        else:
            i += 1

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and datetime.strptime(t["due"], "%Y-%m-%d").date() < today]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    data = load_data()
    if not args:
        error("done requires an ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if tid not in data["tasks"]:
        error(f"No such task: {tid}")

    # Save history
    data["history"].append({
        "type": "done",
        "task_id": tid,
        "prev_tasks": dict(data["tasks"]),
    })

    data["tasks"][tid]["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args):
    data = load_data()
    if not args:
        error("delete requires an ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if tid not in data["tasks"]:
        error(f"No such task: {tid}")

    # Save history
    data["history"].append({
        "type": "delete",
        "task_id": tid,
        "task_data": dict(data["tasks"][tid]),
        "prev_next_id": data["next_id"],
        "prev_tasks": dict(data["tasks"]),
    })

    del data["tasks"][tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args):
    data = load_data()
    if not args:
        error("edit requires an ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    if tid not in data["tasks"]:
        error(f"No such task: {tid}")

    # Parse --title NEW TITLE...
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            title_parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            continue
        i += 1

    if new_title is None:
        error("edit requires --title")

    # Save history
    data["history"].append({
        "type": "edit",
        "task_id": tid,
        "prev_tasks": dict(data["tasks"]),
    })

    data["tasks"][tid]["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args):
    data = load_data()
    if not args:
        error("search requires TEXT")

    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    data = load_data()
    if not args or args[0] != "--format":
        error("export requires --format json|csv")

    fmt = args[1] if len(args) > 1 else ""
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

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
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    data = load_data()
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")

    entry = data["history"].pop()
    data["tasks"] = entry["prev_tasks"]
    if "prev_next_id" in entry:
        data["next_id"] = entry["prev_next_id"]
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

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd in COMMANDS:
        COMMANDS[cmd](args)
    else:
        error(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
