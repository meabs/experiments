#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(tasks, next_id):
    history = load_undo_history()
    history.append({
        "tasks": copy.deepcopy(tasks),
        "next_id": next_id
    })
    save_undo_history(history)


def pop_undo():
    history = load_undo_history()
    if not history:
        return None
    entry = history.pop()
    save_undo_history(history)
    return entry["tasks"], entry["next_id"]


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(priority))
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: {}".format(due))
            i += 2
        else:
            if title is None:
                title = args[i]
                i += 1
            else:
                title += " " + args[i]
                i += 1

    if title is None:
        error("No title provided")

    tasks, next_id = load_tasks()
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due
    }
    push_undo(tasks, next_id)
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print("Added {}".format(next_id))


def cmd_list(args):
    tasks, _ = load_tasks()
    sort_priority = False
    filter_tag = None
    overdue = False
    today_arg = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing --today value")
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue and today_arg is None:
        today_str = date.today().isoformat()
    else:
        today_str = today_arg if today_arg else date.today().isoformat()

    filtered = list(tasks)

    if filter_tag:
        filtered = [t for t in filtered if filter_tag in t.get("tags", [])]

    if overdue:
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error("Invalid date: {}".format(today_str))
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))
    tasks, next_id = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            push_undo(tasks, next_id)
            task["done"] = True
            save_tasks(tasks, next_id)
            print("Done {}".format(task_id))
            return
    error("No such task: {}".format(task_id))


def cmd_delete(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))
    tasks, next_id = load_tasks()
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            push_undo(tasks, next_id)
            tasks.pop(i)
            save_tasks(tasks, next_id)
            print("Deleted {}".format(task_id))
            return
    error("No such task: {}".format(task_id))


def cmd_edit(args):
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1

    if new_title is None:
        error("No new title provided")

    tasks, next_id = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            push_undo(tasks, next_id)
            task["title"] = new_title
            save_tasks(tasks, next_id)
            print("Edited {}".format(task_id))
            return
    error("No such task: {}".format(task_id))


def cmd_search(args):
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
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

    tasks, _ = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due")
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            writer.writerow([
                task["id"],
                task["title"],
                str(task["done"]).lower(),
                task.get("priority", "medium"),
                tags_str,
                due_str
            ])
        print(output.getvalue().rstrip("\n"))
    else:
        error("Invalid format: {}".format(fmt))


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


def cmd_undo(args):
    result = pop_undo()
    if result is None:
        error("Nothing to undo")
    tasks, next_id = result
    save_tasks(tasks, next_id)
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
        error("Unknown command: {}".format(command))

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
