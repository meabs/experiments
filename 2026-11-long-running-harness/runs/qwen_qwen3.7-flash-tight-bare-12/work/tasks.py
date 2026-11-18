#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task(task):
    line = "{} [{}] {}".format(task["id"], "x" if task["done"] else " ", task["title"])
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


def cmd_add(args):
    tasks = load_tasks()
    undo_history = load_undo_history()
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                date.fromisoformat(due_str)
            except ValueError:
                print("Invalid date: {}".format(due_str), file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    task_id = next_id(tasks)
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    undo_history.append(json.dumps(tasks))
    save_undo_history(undo_history)
    print("Added {}".format(task_id))


def cmd_list(args):
    tasks = load_tasks()
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_priority = args[i + 1] == "priority"
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
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
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    tasks = load_tasks()
    undo_history = load_undo_history()
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    undo_history.append(json.dumps(tasks))
    save_undo_history(undo_history)
    print("Done {}".format(task_id))


def cmd_delete(args):
    tasks = load_tasks()
    undo_history = load_undo_history()
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    found = False
    new_tasks = []
    for task in tasks:
        if task["id"] == task_id:
            found = True
        else:
            new_tasks.append(task)
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    save_tasks(new_tasks)
    undo_history.append(json.dumps(tasks))
    save_undo_history(undo_history)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    tasks = load_tasks()
    undo_history = load_undo_history()
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    undo_history.append(json.dumps(tasks))
    save_undo_history(undo_history)
    print("Edited {}".format(task_id))


def cmd_search(args):
    tasks = load_tasks()
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args):
    tasks = load_tasks()
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
    tasks = sorted(tasks, key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print("{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t.get("priority", "medium"), tags_str, due_str))
    else:
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    undo_history = load_undo_history()
    if not undo_history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = undo_history.pop()
    save_undo_history(undo_history)
    tasks = json.loads(prev_state)
    save_tasks(tasks)
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
    command, rest = parse_args(sys.argv[1:])
    handler = COMMANDS.get(command)
    if handler is None:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    handler(rest)


def parse_args(argv):
    if not argv:
        print("No command specified", file=sys.stderr)
        sys.exit(1)
    return argv[0], argv[1:]


if __name__ == "__main__":
    main()
