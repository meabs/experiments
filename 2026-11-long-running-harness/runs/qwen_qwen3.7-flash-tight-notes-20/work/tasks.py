#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except FileNotFoundError:
        return [], 1


def save_data(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(history, tasks, next_id):
    snapshot = {"tasks": copy.deepcopy(tasks), "next_id": next_id}
    history.append(snapshot)
    save_history(history)


def format_task(task):
    status = "x" if task["done"] else " "
    line = '{} [{}] {}'.format(task["id"], status, task["title"])
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        tag_suffix = " ".join("#{}".format(t) for t in task["tags"])
        line += " " + tag_suffix
    if task["due"]:
        line += " due:{}".format(task["due"])
    return line


def cmd_add(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
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
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(due_str), file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    if not title_parts:
        print("Title is required", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks, next_id = load_data()
    history = load_history()
    push_history(history, tasks, next_id)

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
    save_data(tasks, next_id)
    print("Added {}".format(task["id"]))


def cmd_list(args):
    tasks, next_id = load_data()
    sort_priority = False
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
            sort_option = args[i + 1]
            if sort_option != "priority":
                print("Unknown sort option: {}".format(sort_option), file=sys.stderr)
                sys.exit(1)
            sort_priority = True
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
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(format_task(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    task_id = int(args[0])
    tasks, next_id = load_data()
    history = load_history()

    found = None
    for task in tasks:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_history(history, tasks, next_id)
    found["done"] = True
    save_data(tasks, next_id)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    task_id = int(args[0])
    tasks, next_id = load_data()
    history = load_history()

    found_idx = None
    for idx, task in enumerate(tasks):
        if task["id"] == task_id:
            found_idx = idx
            break

    if found_idx is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_history(history, tasks, next_id)
    del tasks[found_idx]
    save_data(tasks, next_id)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    task_id = None
    new_title = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
            while i < len(args) and not args[i].startswith("--"):
                new_title += " " + args[i]
                i += 1
        elif task_id is None:
            task_id = int(arg)
            i += 1
        else:
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)

    if task_id is None or new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_data()
    history = load_history()

    found = None
    for task in tasks:
        if task["id"] == task_id:
            found = task
            break

    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_history(history, tasks, next_id)
    found["title"] = new_title
    save_data(tasks, next_id)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    tasks, next_id = load_data()

    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print("Unknown format: {}".format(fmt), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)

    if not fmt:
        print("--format is required", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_data()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task["tags"],
                "due": task["due"],
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in tasks:
            writer.writerow([
                task["id"],
                task["title"],
                "true" if task["done"] else "false",
                task["priority"],
                ";".join(task["tags"]),
                task["due"] if task["due"] else "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args):
    tasks, next_id = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    tasks, next_id = load_data()
    history = load_history()

    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    snapshot = history.pop()
    save_history(history)
    save_data(snapshot["tasks"], snapshot["next_id"])
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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
