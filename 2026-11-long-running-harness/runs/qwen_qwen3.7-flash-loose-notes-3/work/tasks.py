#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "next_id": 1}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_undo(data):
    history = load_undo_history()
    history.append({"tasks": data["tasks"], "next_id": data["next_id"]})
    save_undo_history(history)


def pop_undo():
    history = load_undo_history()
    if not history:
        return None
    prev = history.pop()
    save_undo_history(history)
    return prev


def format_task(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def cmd_add(args):
    data = load_data()
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
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
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except ValueError:
                print("Invalid date: {}".format(due), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    push_undo(data)

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
    print("Added {}".format(task_id))


def cmd_list(args):
    data = load_data()
    if not data["tasks"]:
        print("No tasks")
        return

    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

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
            i += 2

    tasks = list(data["tasks"])

    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if overdue:
        if today_str:
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    for t in tasks:
        print(format_task(t))


def cmd_done(args):
    data = load_data()
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    task = find_task(data, task_id)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_undo(data)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(args):
    data = load_data()
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    task = find_task(data, task_id)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    data = load_data()
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    task = find_task(data, task_id)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            continue
        i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(args):
    data = load_data()
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()

    matches = [t for t in data["tasks"] if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task(t))


def cmd_export(args):
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

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
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            writer.writerow([t["id"], t["title"], done_str,
                             t.get("priority", "medium"), tags_str, due_str])
        print(output.getvalue(), end="")
    else:
        print("Unknown format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    prev = pop_undo()
    if prev is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    data = {
        "tasks": prev["tasks"],
        "next_id": prev["next_id"],
    }
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
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
