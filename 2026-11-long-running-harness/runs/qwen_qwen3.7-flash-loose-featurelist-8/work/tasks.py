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
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def snapshot(data):
    return {"tasks": list(data["tasks"]), "next_id": data["next_id"]}


def record_undo(data, snap):
    data["history"].append(snap)

def format_task_line(task):
    done_marker = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_marker} {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def do_add(args, data):
    priority = "medium"
    tags = []
    due = None
    flag_start = len(args)
    for idx, arg in enumerate(args):
        if arg in ("--priority", "--tag", "--due"):
            flag_start = idx
            break
    title_parts = args[:flag_start]
    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    i = flag_start
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                parts = due_str.split("-")
                if len(parts) != 3:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
                due = due_str
            except (ValueError, OverflowError):
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1
    snap = snapshot(data)
    record_undo(data, snap)
    task = {"id": data["next_id"], "title": title, "done": False,
            "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def do_list(args, data):
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            if sort_by != "priority":
                print(f"Unknown sort: {sort_by}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing today value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    today = date.fromisoformat(today_str) if today_str else date.today()
    tasks = list(data["tasks"])
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = date.fromisoformat(t["due"])
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def do_done(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    snap = snapshot(data)
    record_undo(data, snap)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def do_delete(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    snap = snapshot(data)
    record_undo(data, snap)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            rest = args[i + 1:]
            if not rest:
                print("Missing title after --title", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(rest)
            break
        i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    snap = snapshot(data)
    record_undo(data, snap)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def do_search(args, data):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"], key=lambda t: t["id"]):
        if text in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def do_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Unknown format: {fmt}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1
    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({"id": t["id"], "title": t["title"],
                "done": t["done"], "priority": t["priority"],
                "tags": t.get("tags", []), "due": t.get("due")})
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def do_stats(args, data):
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(args, data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


COMMANDS = {
    "add": do_add, "list": do_list, "done": do_done,
    "delete": do_delete, "edit": do_edit, "search": do_search,
    "export": do_export, "stats": do_stats, "undo": do_undo,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    COMMANDS[cmd](sys.argv[2:], data)
    save_data(data)


if __name__ == "__main__":
    main()
