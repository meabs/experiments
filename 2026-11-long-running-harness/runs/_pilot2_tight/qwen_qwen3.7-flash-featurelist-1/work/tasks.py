#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    if task.get("tags"):
        for tag in task["tags"]:
            parts.append(f"#{tag}")
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


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
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        print("Error: TITLE is required", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    snapshot = {"tasks": list(data["tasks"]), "next_id": data["next_id"]}
    task_id = data["next_id"]
    data["next_id"] += 1
    task = {"id": task_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    data["undo_stack"].append({"action": "add", "snapshot": snapshot})
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    sort_mode = None
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    tasks = data["tasks"]
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today.isoformat()]
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    if not args:
        print("Error: ID is required", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    snapshot = {"tasks": list(data["tasks"]), "next_id": data["next_id"]}
    task["done"] = True
    data["undo_stack"].append({"action": "done", "snapshot": snapshot})
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        print("Error: ID is required", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    snapshot = {"tasks": list(data["tasks"]), "next_id": data["next_id"]}
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    data["undo_stack"].append({"action": "delete", "snapshot": snapshot})
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        print("Error: ID is required", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title_parts.append(args[i + 1])
            i += 2
        else:
            i += 1
    if not new_title_parts:
        print("--title is required", file=sys.stderr)
        sys.exit(1)
    snapshot = {"tasks": list(data["tasks"]), "next_id": data["next_id"]}
    task["title"] = " ".join(new_title_parts)
    data["undo_stack"].append({"action": "edit", "snapshot": snapshot})
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        print("Error: TEXT is required", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()
    matches = [t for t in data["tasks"] if search_text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in sorted(matches, key=lambda t: t["id"]):
        print(task_line(task))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not fmt:
        print("--format is required", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_tasks = [{"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"], "tags": t.get("tags", []), "due": t.get("due")} for t in tasks]
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    entry = data["undo_stack"].pop()
    data["tasks"] = entry["snapshot"]["tasks"]
    data["next_id"] = entry["snapshot"]["next_id"]
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
