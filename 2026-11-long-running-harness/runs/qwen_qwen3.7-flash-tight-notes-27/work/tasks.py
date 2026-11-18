#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


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
        json.dump(data, f)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def push_history(data):
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })


def cmd_add(args):
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(due_str), file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            break
    title = " ".join(args[:i])
    if not title:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    push_history(data)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print("Added {}".format(task["id"]))


def cmd_list(args):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                print("Unknown sort option: {}".format(args[i + 1]), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a date value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            print("Unknown argument: {}".format(args[i]), file=sys.stderr)
            sys.exit(1)
    data = load_data()
    tasks = data["tasks"]
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today_str is None:
            today = date.today().isoformat()
        else:
            today = today_str
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    task_idx = None
    for idx, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            task = t
            task_idx = idx
            break
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    data["tasks"].pop(task_idx)
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid task id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    remaining = args[1:]
    title = None
    i = 0
    while i < len(remaining):
        if remaining[i] == "--title":
            if i + 1 >= len(remaining):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            title = " ".join(remaining[i + 1:])
            break
        else:
            print("Unknown argument: {}".format(remaining[i]), file=sys.stderr)
            sys.exit(1)
        i += 1
    if title is None:
        print("Missing --title flag", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    task["title"] = title
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    data = load_data()
    matches = []
    for task in data["tasks"]:
        if query in task["title"].lower():
            matches.append(task)
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print("Invalid format: {}".format(fmt), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print("Unknown argument: {}".format(args[i]), file=sys.stderr)
            sys.exit(1)
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    data = load_data()
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
                "due": t.get("due", None),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str
            ))


def cmd_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
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
    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
