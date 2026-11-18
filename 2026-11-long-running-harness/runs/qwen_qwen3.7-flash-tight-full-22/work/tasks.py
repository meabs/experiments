#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = data.get("tasks", [])
    next_id = data.get("next_id", 1)
    return tasks, next_id


def save_tasks(tasks, next_id):
    data = {"tasks": tasks, "next_id": next_id}
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


def format_task(task):
    done_mark = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], done_mark, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        tag_str = " ".join("#{}".format(t) for t in tags)
        line += " {}".format(tag_str)
    due = task.get("due", None)
    if due:
        line += " due:{}".format(due)
    return line


def push_history(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_history(history)


def cmd_add(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Invalid date: ", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                parts = due.split("-")
                if len(parts) != 3:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, OverflowError):
                print("Invalid date: {}".format(due), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    push_history(tasks, next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    next_id += 1
    save_tasks(tasks, next_id)
    print("Added {}".format(next_id - 1))


def cmd_list(args):
    tasks, next_id = load_tasks()
    sort_priority = False
    filter_tag = None
    overdue = False
    today = date.today().isoformat()
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_option = args[i + 1]
            if sort_option == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a date", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    if not args or not args[0].isdigit():
        print("Error: done requires an ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(tasks, next_id)
    save_tasks(tasks, next_id)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args or not args[0].isdigit():
        print("Error: delete requires an ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(tasks, next_id)
    save_tasks(new_tasks, next_id)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args or not args[0].isdigit():
        print("Error: edit requires an ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        print("Error: edit requires --title", file=sys.stderr)
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
    push_history(tasks, next_id)
    save_tasks(tasks, next_id)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Error: search requires text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    tasks, next_id = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Error: --format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Error: export requires --format json or --format csv", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    tasks = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due", None),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due", "")
            done_str = "true" if task["done"] else "false"
            print("{},{},{},{},{},{}".format(
                task["id"], task["title"], done_str,
                task.get("priority", "medium"), tags_str, due_str
            ))
    else:
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, next_id = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_history(history)
    save_tasks(previous["tasks"], previous["next_id"])
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
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
