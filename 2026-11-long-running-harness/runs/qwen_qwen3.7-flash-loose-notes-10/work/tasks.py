#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


TASKS_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {"tasks": [], "next_id": 1}
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    with open(TASKS_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(history, data):
    history.append(json.loads(json.dumps(data)))
    save_undo_history(history)


def format_task_line(task):
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    title = task["title"]
    suffixes = []
    if task.get("priority") == "high":
        suffixes.append("(high)")
    elif task.get("priority") == "low":
        suffixes.append("(low)")
    for tag in task.get("tags", []):
        suffixes.append("#" + tag)
    if task.get("due"):
        suffixes.append("due:" + task["due"])
    if suffixes:
        return str(tid) + " " + status + " " + title + " " + " ".join(suffixes)
    return str(tid) + " " + status + " " + title


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def parse_add_args(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            i += 1
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: " + priority)
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            i += 1
            tags.append(args[i])
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            i += 1
            due = args[i]
            try:
                parts = due.split("-")
                if len(parts) != 3:
                    raise ValueError
                date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                error("Invalid date: " + due)
        else:
            title_parts.append(arg)
        i += 1
    return title_parts, priority, tags, due


def cmd_add(args, data, history):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title_parts, priority, tags, due = parse_add_args(args)
    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = " ".join(title_parts)
    push_undo(history, data)
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
    save_tasks(data)
    print("Added " + str(task_id))


def cmd_list(args, data, history):
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            i += 1
            if args[i] != "priority":
                error("Unknown sort option: " + args[i])
            sort_priority = True
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            i += 1
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            i += 1
            today_str = args[i]
            try:
                parts = today_str.split("-")
                date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                error("Invalid date: " + today_str)
        i += 1
    tasks = list(data["tasks"])
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        if today_str:
            parts = today_str.split("-")
            today = date(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            today = date.today()
            today_str = str(today)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    if sort_priority:
        porder = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data, history):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: " + str(task_id))
    push_undo(history, data)
    task["done"] = True
    save_tasks(data)
    print("Done " + str(task_id))


def cmd_delete(args, data, history):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: " + str(task_id))
    push_undo(history, data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_tasks(data)
    print("Deleted " + str(task_id))


def cmd_edit(args, data, history):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error("No such task: " + str(task_id))
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            while i < len(args):
                if args[i].startswith("--"):
                    break
                new_title_parts.append(args[i])
                i += 1
            break
        i += 1
    if not new_title_parts:
        error("Usage: edit ID --title NEW TITLE")
    new_title = " ".join(new_title_parts)
    push_undo(history, data)
    task["title"] = new_title
    save_tasks(data)
    print("Edited " + str(task_id))


def cmd_search(args, data, history):
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    matches = []
    for task in data["tasks"]:
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data, history):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            i += 1
            fmt = args[i]
            if fmt not in ("json", "csv"):
                error("Unknown format: " + fmt)
        i += 1
    if fmt is None:
        error("Usage: export --format json|csv")
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_val = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(str(t["id"]) + "," + t["title"] + "," + done_str + "," + t.get("priority", "medium") + "," + tags_str + "," + due_val)


def cmd_stats(args, data, history):
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total))


def cmd_undo(args, data, history):
    if not history:
        error("Nothing to undo")
    prev_data = history.pop()
    save_undo_history(history)
    data["tasks"] = prev_data["tasks"]
    data["next_id"] = prev_data["next_id"]
    save_tasks(data)
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
        error("Unknown command: " + command)
    args = sys.argv[2:]
    data = load_tasks()
    history = load_undo_history()
    COMMANDS[command](args, data, history)


if __name__ == "__main__":
    main()
