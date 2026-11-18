#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    converted = {}
    for k, v in data.get("tasks", {}).items():
        converted[int(k)] = v
    data["tasks"] = converted
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def print_error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    p = task.get("priority", "medium")
    if p == "high":
        line += " (high)"
    elif p == "low":
        line += " (low)"
    for tag in task.get("tags", []):
        line += " #{}".format(tag)
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def do_add(args, data):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print_error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print_error("Invalid priority: {}".format(priority))
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print_error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print_error("Missing due date value")
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except ValueError:
                print_error("Invalid date: {}".format(due))
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        print_error("Missing task title")
    title = " ".join(title_parts)
    history = load_history()
    history.append({
        "type": "add",
        "state": {"tasks": dict(data["tasks"]), "next_id": data["next_id"]}
    })
    save_history(history)
    task_id = data["next_id"]
    data["next_id"] += 1
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due
    }
    save_data(data)
    print("Added {}".format(task_id))


def do_list(args, data):
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    today = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print_error("Missing sort value")
            sort_by = args[i + 1]
            if sort_by != "priority":
                print_error("Invalid sort: {}".format(sort_by))
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print_error("Missing tag value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print_error("Missing today date")
            today_str = args[i + 1]
            try:
                today = date.fromisoformat(today_str)
            except ValueError:
                print_error("Invalid date: {}".format(today_str))
            i += 2
        else:
            print_error("Unknown option: {}".format(arg))
    if overdue and today is None:
        today = date.today()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        filtered = []
        for t in tasks:
            if not t["done"] and t.get("due"):
                try:
                    due_date = date.fromisoformat(t["due"])
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def do_done(args, data):
    if not args:
        print_error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        print_error("Invalid id: {}".format(args[0]))
    if task_id not in data["tasks"]:
        print_error("No such task: {}".format(task_id))
    history = load_history()
    history.append({
        "type": "done",
        "state": {"tasks": dict(data["tasks"]), "next_id": data["next_id"]}
    })
    save_history(history)
    data["tasks"][task_id]["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def do_delete(args, data):
    if not args:
        print_error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        print_error("Invalid id: {}".format(args[0]))
    if task_id not in data["tasks"]:
        print_error("No such task: {}".format(task_id))
    history = load_history()
    history.append({
        "type": "delete",
        "state": {"tasks": dict(data["tasks"]), "next_id": data["next_id"]}
    })
    save_history(history)
    del data["tasks"][task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def do_edit(args, data):
    if not args:
        print_error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        print_error("Invalid id: {}".format(args[0]))
    if task_id not in data["tasks"]:
        print_error("No such task: {}".format(task_id))
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print_error("Missing title value")
            new_title = " ".join(args[i + 1:])
            break
        else:
            print_error("Unknown option: {}".format(args[i]))
        i += 1
    if new_title is None:
        print_error("Missing --title flag")
    history = load_history()
    history.append({
        "type": "edit",
        "state": {"tasks": dict(data["tasks"]), "next_id": data["next_id"]}
    })
    save_history(history)
    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def do_search(args, data):
    if not args:
        print_error("Missing search text")
    search_text = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if search_text in t["title"].lower()]
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
                print_error("Missing format value")
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print_error("Invalid format: {}".format(fmt))
            i += 2
        else:
            print_error("Unknown option: {}".format(args[i]))
            i += 1
    if fmt is None:
        print_error("Missing --format flag")
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due")
            })
        print(json.dumps(result))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", "")
            ])
        print(output.getvalue().rstrip("\n"))


def do_stats(args, data):
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(list(tasks))
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def do_undo(args, data):
    history = load_history()
    if not history:
        print_error("Nothing to undo")
    last = history.pop()
    save_history(history)
    data["tasks"] = last["state"]["tasks"]
    data["next_id"] = last["state"]["next_id"]
    save_data(data)
    print("Undone")


COMMANDS = {
    "add": do_add,
    "list": do_list,
    "done": do_done,
    "delete": do_delete,
    "edit": do_edit,
    "search": do_search,
    "export": do_export,
    "stats": do_stats,
    "undo": do_undo,
}


def main():
    if len(sys.argv) < 2:
        print_error("Usage: python3 tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        print_error("Unknown command: {}".format(command))
    data = load_data()
    COMMANDS[command](sys.argv[2:], data)


if __name__ == "__main__":
    main()
