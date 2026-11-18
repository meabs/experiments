#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return {"tasks": [], "next_id": 1, "undo_history": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task(task):
    check = "x" if task["done"] else " "
    line = str(task["id"]) + " [" + check + "] " + task["title"]
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    for tag in task["tags"]:
        line += " #" + tag
    if task["due"]:
        line += " due:" + task["due"]
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("--priority requires a value")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("--due requires a value")
            due = args[i]
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, IndexError):
                error(f"Invalid date: {due}")
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            title_parts.append(arg)
        i += 1
    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = " ".join(title_parts)
    data = load_data()
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["undo_history"].append(snapshot)
    new_task = {"id": data["next_id"], "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(new_task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {new_task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"])
    if not tasks:
        print("No tasks")
        return
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            i += 1
            if i >= len(args):
                error("--sort requires a value")
            if args[i] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i]}")
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            tag_filter = args[i]
        elif args[i] == "--overdue":
            overdue = True
        elif args[i] == "--today":
            i += 1
            if i >= len(args):
                error("--today requires a value")
            today_str = args[i]
        else:
            error(f"Unknown option: {args[i]}")
        i += 1
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today]
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


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    data = load_data()
    for t in data["tasks"]:
        if t["id"] == task_id:
            if t["done"]:
                print(f"Task {task_id} is already done")
                return
            snapshot = {"tasks": [dict(td) for td in data["tasks"]], "next_id": data["next_id"]}
            data["undo_history"].append(snapshot)
            t["done"] = True
            save_data(data)
            print(f"Done {task_id}")
            return
    error(f"No such task: {task_id}")


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    data = load_data()
    for idx, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            snapshot = {"tasks": [dict(td) for td in data["tasks"]], "next_id": data["next_id"]}
            data["undo_history"].append(snapshot)
            data["tasks"].pop(idx)
            save_data(data)
            print(f"Deleted {task_id}")
            return
    error(f"No such task: {task_id}")


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    title_idx = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_idx = i
            break
    if title_idx is None:
        error("Usage: edit ID --title NEW TITLE")
    if title_idx + 1 >= len(args):
        error("--title requires a value")
    new_title = " ".join(args[title_idx + 1:])
    data = load_data()
    for t in data["tasks"]:
        if t["id"] == task_id:
            snapshot = {"tasks": [dict(td) for td in data["tasks"]], "next_id": data["next_id"]}
            data["undo_history"].append(snapshot)
            t["title"] = new_title
            save_data(data)
            print(f"Edited {task_id}")
            return
    error(f"No such task: {task_id}")


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    data = load_data()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                error("--format requires a value")
            fmt = args[i]
        else:
            error(f"Unknown option: {args[i]}")
        i += 1
    if not fmt:
        error("Usage: export --format json|csv")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"], "tags": t["tags"], "due": t["due"]})
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t['priority']},{tags_str},{due_str}")


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
    history = data.get("undo_history", [])
    if not history:
        error("Nothing to undo")
    previous = history.pop()
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")
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
        error(f"Unknown command: {command}")
    commands[command](args)


if __name__ == "__main__":
    main()
