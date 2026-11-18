#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due_str = args[i + 1]
            try:
                date.fromisoformat(due_str)
            except ValueError:
                error(f"Invalid date: {due_str}")
            due = due_str
            i += 2
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        error("Missing task title")
    title = " ".join(title_parts)
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
    data["history"].append({
        "type": "add",
        "task_id": task["id"],
        "prev_next_id": data["next_id"] - 1,
    })
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args, data):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing today value")
            today_str = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks
                 if not t["done"]
                 and t.get("due")
                 and date.fromisoformat(t["due"]) < today]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task(task))


def cmd_done(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")
    data["history"].append({
        "type": "done",
        "task_id": task_id,
        "old_done": task["done"],
    })
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")
    data["history"].append({
        "type": "delete",
        "task_id": task_id,
        "task": dict(task),
    })
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")
    new_title = None
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing new title")
            new_title = " ".join(args[i + 1:])
            break
        else:
            error(f"Unknown option: {arg}")
    if new_title is None:
        error("Missing --title")
    data["history"].append({
        "type": "edit",
        "task_id": task_id,
        "old_title": task["title"],
    })
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if fmt is None:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
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
        print(json.dumps(export_tasks))
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
                t.get("due") or "",
            ])
        print(output.getvalue().rstrip("\n"))


def cmd_stats(args, data):
    if args:
        error("stats takes no arguments")
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if args:
        error("undo takes no arguments")
    history = data.get("history", [])
    if not history:
        error("Nothing to undo")
    last_action = history.pop()
    action_type = last_action["type"]
    if action_type == "add":
        task_id = last_action["task_id"]
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        data["next_id"] = last_action["prev_next_id"]
    elif action_type == "done":
        task_id = last_action["task_id"]
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task:
            task["done"] = last_action["old_done"]
    elif action_type == "delete":
        task = last_action["task"]
        data["tasks"].append(task)
        data["tasks"].sort(key=lambda t: t["id"])
    elif action_type == "edit":
        task_id = last_action["task_id"]
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task:
            task["title"] = last_action["old_title"]
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
    args = sys.argv[2:]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
