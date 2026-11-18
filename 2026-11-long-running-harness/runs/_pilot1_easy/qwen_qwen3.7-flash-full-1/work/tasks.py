#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


TASKS_FILE = "tasks.json"


def load_data():
    if not os.path.exists(TASKS_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(TASKS_FILE, "r") as f:
        data = json.load(f)
    if isinstance(data.get("tasks"), dict):
        new_tasks = {}
        for k, v in data["tasks"].items():
            new_tasks[str(k)] = v
        data["tasks"] = new_tasks
    else:
        data["tasks"] = {}
    return data


def save_data(data):
    with open(TASKS_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
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


def cmd_add(args, data):
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
                due = due_str
            except ValueError:
                error(f"Invalid date: {due_str}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("No title provided")
    title = " ".join(title_parts)
    task_id = data["next_id"]
    key = str(task_id)
    data["tasks"][key] = {
        "id": task_id, "title": title, "done": False,
        "priority": priority, "tags": tags, "due": due,
    }
    data["next_id"] = task_id + 1
    data["history"].append({"type": "add", "task_id": task_id, "prev_next_id": task_id})
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    today = date.today()
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            i += 1
    tasks = list(data["tasks"].values())
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered
    if sort_priority:
        porder = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(format_task(t))


def cmd_done(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")
    data["tasks"][key]["done"] = True
    data["history"].append({"type": "done", "task_id": task_id, "was_done": False})
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")
    deleted_task = data["tasks"].pop(key)
    data["history"].append({"type": "delete", "task_id": task_id, "task": deleted_task})
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        i += 1
    if new_title is None:
        error("No --title provided")
    old_title = data["tasks"][key]["title"]
    data["tasks"][key]["title"] = new_title
    data["history"].append({"type": "edit", "task_id": task_id, "old_title": old_title})
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    matches = []
    for t in sorted(data["tasks"].values(), key=lambda x: x["id"]):
        if query in t["title"].lower():
            matches.append(t)
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task(t))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"], "title": t["title"], "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []), "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority','medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if not data["history"]:
        error("Nothing to undo")
    action = data["history"].pop()
    if action["type"] == "add":
        tid = action["task_id"]
        key = str(tid)
        if key in data["tasks"]:
            del data["tasks"][key]
        data["next_id"] = action["prev_next_id"]
    elif action["type"] == "done":
        tid = action["task_id"]
        key = str(tid)
        if key in data["tasks"]:
            data["tasks"][key]["done"] = action["was_done"]
    elif action["type"] == "delete":
        tid = action["task_id"]
        key = str(tid)
        data["tasks"][key] = action["task"]
    elif action["type"] == "edit":
        tid = action["task_id"]
        key = str(tid)
        if key in data["tasks"]:
            data["tasks"][key]["title"] = action["old_title"]
    save_data(data)
    print("Undone")


COMMANDS = {
    "add": cmd_add, "list": cmd_list, "done": cmd_done,
    "delete": cmd_delete, "edit": cmd_edit, "search": cmd_search,
    "export": cmd_export, "stats": cmd_stats, "undo": cmd_undo,
}


def main():
    if len(sys.argv) < 2:
        error("Usage: tasks.py <command> [args]")
    command = sys.argv[1]
    args = sys.argv[2:]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
