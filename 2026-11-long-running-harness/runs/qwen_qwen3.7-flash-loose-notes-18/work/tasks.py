#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    data.setdefault("tasks", [])
    data.setdefault("next_id", 1)
    data.setdefault("history", [])
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def snapshot(data):
    return {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }


def format_task(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    if task["tags"]:
        parts.append(" ".join(f"#{tag}" for tag in task["tags"]))
    if task["due"]:
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def add_task(args):
    if len(args) < 1:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
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
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                date.fromisoformat(due_str)
            except (ValueError, TypeError):
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    old = snapshot(data)
    data["history"].append(old)

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


def list_tasks(args):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_val = args[i + 1]
            if sort_val != "priority":
                print(f"Unknown sort option: {sort_val}", file=sys.stderr)
                sys.exit(1)
            sort_priority = True
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
                print("--today requires a value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    data = load_data()
    tasks = list(data["tasks"])

    if not tasks:
        print("No tasks")
        return

    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    if overdue:
        if today_str is not None:
            try:
                today = date.fromisoformat(today_str)
            except (ValueError, TypeError):
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t["due"] is not None and date.fromisoformat(t["due"]) < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(format_task(t))


def done_task(args):
    if len(args) != 1:
        print("Usage: done ID", file=sys.stderr)
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

    old = snapshot(data)
    data["history"].append(old)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def delete_task(args):
    if len(args) != 1:
        print("Usage: delete ID", file=sys.stderr)
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

    old = snapshot(data)
    data["history"].append(old)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def edit_task(args):
    if len(args) < 1:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    task_id_str = args[0]
    try:
        task_id = int(task_id_str)
    except ValueError:
        print(f"No such task: {task_id_str}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
            while i < len(args):
                new_title += " " + args[i]
                i += 1
        else:
            i += 1

    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
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

    old = snapshot(data)
    data["history"].append(old)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def search_tasks(args):
    if len(args) < 1:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args)
    data = load_data()
    matches = []
    for t in data["tasks"]:
        if query.lower() in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
        return

    matches.sort(key=lambda t: t["id"])
    for t in matches:
        print(format_task(t))


def export_tasks(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Unknown format: {fmt}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def stats_tasks(args):
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def undo_command(args):
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    old = data["history"].pop()
    data["tasks"] = old["tasks"]
    data["next_id"] = old["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "add": add_task,
        "list": list_tasks,
        "done": done_task,
        "delete": delete_task,
        "edit": edit_task,
        "search": search_tasks,
        "export": export_tasks,
        "stats": stats_tasks,
        "undo": undo_command,
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args)


if __name__ == "__main__":
    main()
