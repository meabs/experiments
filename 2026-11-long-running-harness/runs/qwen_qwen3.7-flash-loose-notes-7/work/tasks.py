#!/usr/bin/env python3
import csv
import io
import json
import sys
from datetime import date

DATA_FILE = "tasks.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"tasks": [], "next_id": 1, "undo_history": []}
    data.setdefault("tasks", [])
    data.setdefault("next_id", 1)
    data.setdefault("undo_history", [])
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def validate_date(date_str):
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
    except (ValueError, IndexError):
        error(f"Invalid date: {date_str}")
    return date_str

def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line

def cmd_add(args):
    priority = "medium"
    tags = []
    due = None
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due = validate_date(args[i + 1])
            i += 2
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            positional.append(arg)
            i += 1
    if not positional:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = " ".join(positional)
    data = load_data()
    # Save undo snapshot BEFORE mutation
    data["undo_history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
    task = {"id": data["next_id"], "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")

def cmd_list(args):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today_str = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")
    data = load_data()
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today_str:
            validate_date(today_str)
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]
    if sort_priority:
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(task_line(task))

def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    # Save undo snapshot BEFORE mutation
    data["undo_history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")

def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    # Save undo snapshot BEFORE mutation
    data["undo_history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")

def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    title_parts = []
    i = 1
    found_title = False
    while i < len(args):
        if args[i] == "--title":
            found_title = True
            i += 1
            title_parts = args[i:]
            break
        else:
            error(f"Unknown option: {args[i]}")
    if not found_title or not title_parts:
        error("Usage: edit ID --title NEW TITLE")
    new_title = " ".join(title_parts)
    # Save undo snapshot BEFORE mutation
    data["undo_history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")

def cmd_search(args):
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args)
    data = load_data()
    matches = [t for t in data["tasks"] if text.lower() in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(task_line(task))

def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if not fmt:
        error("Usage: export --format json|csv")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({"id": t["id"], "title": t["title"], "done": t["done"], "priority": t.get("priority", "medium"), "tags": t.get("tags", []), "due": t.get("due")})
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([t["id"], t["title"], str(t["done"]).lower(), t.get("priority", "medium"), ";".join(t.get("tags", [])), t.get("due") or ""])
        print(output.getvalue(), end="")

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
    prev = data["undo_history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")

COMMANDS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete, "edit": cmd_edit, "search": cmd_search, "export": cmd_export, "stats": cmd_stats, "undo": cmd_undo}

def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    COMMANDS[command](sys.argv[2:])

if __name__ == "__main__":
    main()
