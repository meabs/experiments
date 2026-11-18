#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def make_task_line(task):
    done_marker = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_marker} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        tags_str = " ".join(f"#{t}" for t in task["tags"])
        line += " " + tags_str
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    data = load_data()
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Invalid date: ")
            val = args[i + 1]
            try:
                parsed = datetime.strptime(val, "%Y-%m-%d").date()
                if parsed.strftime("%Y-%m-%d") != val:
                    raise ValueError
            except ValueError:
                error(f"Invalid date: {val}")
            due = val
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("Missing title")
    title = " ".join(title_parts)
    data["history"].append({
        "type": "add",
        "prev_tasks": [dict(t) for t in data["tasks"]],
        "prev_next_id": data["next_id"],
    })
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"])
    if not tasks:
        print("No tasks")
        return
    sort_priority = False
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires an argument")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date")
            val = args[i + 1]
            try:
                today = datetime.strptime(val, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {val}")
            i += 2
        else:
            i += 1
    if overdue and today is None:
        today = date.today()
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today.isoformat()]
    if sort_priority:
        porder = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(make_task_line(t))


def cmd_done(args):
    data = load_data()
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    data["history"].append({
        "type": "done",
        "task_id": task_id,
        "prev_done": task["done"],
        "prev_tasks": [dict(t) for t in data["tasks"]],
        "prev_next_id": data["next_id"],
    })
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    data = load_data()
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    data["history"].append({
        "type": "delete",
        "deleted_task": dict(task),
        "prev_tasks": [dict(t) for t in data["tasks"]],
        "prev_next_id": data["next_id"],
    })
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    data = load_data()
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    title_idx = None
    for idx, arg in enumerate(args):
        if arg == "--title":
            title_idx = idx
            break
    if title_idx is None or title_idx + 1 >= len(args):
        error("Missing --title value")
    new_title = " ".join(args[title_idx + 1:])
    data["history"].append({
        "type": "edit",
        "task_id": task_id,
        "prev_title": task["title"],
        "prev_tasks": [dict(t) for t in data["tasks"]],
        "prev_next_id": data["next_id"],
    })
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    data = load_data()
    if not args:
        print("No matches")
        return
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(make_task_line(t))


def cmd_export(args):
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt is None:
        error("Missing --format argument")
    if fmt == "json":
        output = []
        for t in sorted(data["tasks"], key=lambda x: x["id"]):
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in sorted(data["tasks"], key=lambda x: x["id"]):
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority','medium')},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")
    last = data["history"].pop()
    data["tasks"] = last["prev_tasks"]
    data["next_id"] = last["prev_next_id"]
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
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
