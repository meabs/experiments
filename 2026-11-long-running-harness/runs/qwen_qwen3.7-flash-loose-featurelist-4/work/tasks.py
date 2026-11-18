#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
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


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


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
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, TypeError):
                error(f"Invalid date: {due}")
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        error("Missing title")

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)

    data["undo_history"].append({
        "type": "add",
        "task": dict(task),
        "prev_next_id": data["next_id"],
    })
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return

    sort_mode = "id"
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    if today_str is None:
        today_str = date.today().isoformat()

    filtered = list(tasks)

    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    if overdue:
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    data = load_data()
    if not args:
        error("Missing task ID")
    task_id = int(args[0])

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    data["undo_history"].append({
        "type": "done",
        "task_id": task_id,
        "was_done": task["done"],
    })
    task["done"] = True

    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    data = load_data()
    if not args:
        error("Missing task ID")
    task_id = int(args[0])

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    data["undo_history"].append({
        "type": "delete",
        "task": dict(task),
    })
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    data = load_data()
    if not args:
        error("Missing task ID")
    task_id = int(args[0])

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            new_title = args[i + 1]
            i += 2
            while i < len(args) and not args[i].startswith("--"):
                new_title += " " + args[i]
                i += 1
        else:
            i += 1

    if new_title is None:
        error("Missing --title")

    data["undo_history"].append({
        "type": "edit",
        "task_id": task_id,
        "old_title": task["title"],
    })
    task["title"] = new_title

    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    data = load_data()
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()

    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

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
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

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
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


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
    if not data["undo_history"]:
        error("Nothing to undo")

    snapshot = data["undo_history"].pop()

    if snapshot["type"] == "add":
        task_id = snapshot["task"]["id"]
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        data["next_id"] = snapshot["prev_next_id"]
    elif snapshot["type"] == "done":
        for t in data["tasks"]:
            if t["id"] == snapshot["task_id"]:
                t["done"] = snapshot["was_done"]
                break
    elif snapshot["type"] == "delete":
        data["tasks"].append(snapshot["task"])
        if data["tasks"]:
            data["next_id"] = max(t["id"] for t in data["tasks"]) + 1
    elif snapshot["type"] == "edit":
        for t in data["tasks"]:
            if t["id"] == snapshot["task_id"]:
                t["title"] = snapshot["old_title"]
                break

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

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
