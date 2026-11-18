#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
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
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
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
            try:
                date.fromisoformat(due)
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("Missing task title")
    title = " ".join(title_parts)
    data["history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
    task = {"id": data["next_id"], "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    if not data["tasks"]:
        print("No tasks")
        return
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            if args[i + 1] != "priority":
                error(f"Unknown sort option: {args[i + 1]}")
            sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date value")
            today_str = args[i + 1]
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            i += 1
    if today is None:
        today = date.today()
    tasks = list(data["tasks"])
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]
    if sort_priority:
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task(task))


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
    data["history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
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
    data["history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
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
        else:
            i += 1
    if not new_title_parts:
        error("--title requires a value")
    new_title = " ".join(new_title_parts)
    data["history"].append({"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]})
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
        print(format_task(task))


def cmd_export(args):
    data = load_data()
    fmt = "json"
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                error(f"Unknown format: {fmt}")
            i += 2
        else:
            i += 1
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
                "due": t.get("due", None),
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_val = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            pri = t.get("priority", "medium")
            print(f"{t['id']},{t['title']},{done_str},{pri},{tags_str},{due_val}")


def cmd_stats(args):
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")
    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
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
