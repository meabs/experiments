#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = '{} [{}] {}'.format(task["id"], status, task["title"])
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    for tag in task["tags"]:
        line += " #{}".format(tag)
    if task["due"]:
        line += " due:{}".format(task["due"])
    return line


def do_add(args):
    data = load_data()
    priority = "medium"
    remaining = list(args)
    while remaining:
        if remaining[0] == "--priority":
            if len(remaining) < 2:
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = remaining[1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            remaining = remaining[2:]
        elif remaining[0].startswith("--"):
            print("Unknown option: {}".format(remaining[0]), file=sys.stderr)
            sys.exit(1)
        else:
            break
    if not remaining:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(remaining)
    tags = []
    i = 0
    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        else:
            i += 1
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
                due = due_str
            except ValueError:
                print("Invalid date: {}".format(due_str), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["undo_history"].append(snapshot)
    task = {"id": data["next_id"], "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print("Added {}".format(task["id"]))


def do_list(args):
    data = load_data()
    if not data["tasks"]:
        print("No tasks")
        return
    tasks = list(data["tasks"])
    filter_tag = None
    show_overdue = False
    today_str = None
    sort_by_priority = False
    i = 0
    while i < len(args):
        if args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            show_overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        elif args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort_by_priority = True
            i += 2
        else:
            i += 1
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]
    if show_overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t["due"] and datetime.strptime(t["due"], "%Y-%m-%d").date() < today]
    if sort_by_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    for task in tasks:
        print(format_task_line(task))


def do_done(args):
    data = load_data()
    if not args or not args[0].isdigit():
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["undo_history"].append(snapshot)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def do_delete(args):
    data = load_data()
    if not args or not args[0].isdigit():
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["undo_history"].append(snapshot)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def do_edit(args):
    data = load_data()
    if not args or not args[0].isdigit():
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
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
            new_title = " ".join(args[i + 1:])
            break
        i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["undo_history"].append(snapshot)
    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def do_search(args):
    data = load_data()
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def do_export(args):
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
    if fmt not in ("json", "csv"):
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"], "tags": t["tags"], "due": t["due"]})
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print("{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t["priority"], tags_str, due_str))


def do_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def do_undo(args):
    data = load_data()
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = data["undo_history"].pop()
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
    save_data(data)
    print("Undone")


COMMANDS = {"add": do_add, "list": do_list, "done": do_done, "delete": do_delete, "edit": do_edit, "search": do_search, "export": do_export, "stats": do_stats, "undo": do_undo}


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print("Unknown command: {}".format(cmd), file=sys.stderr)
        sys.exit(1)
    COMMANDS[cmd](sys.argv[2:])


if __name__ == "__main__":
    main()
