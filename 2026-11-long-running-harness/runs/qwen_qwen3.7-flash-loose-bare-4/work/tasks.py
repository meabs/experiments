#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = {int(k): v for k, v in data["tasks"].items()}
    return tasks, data["next_id"]


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def append_history(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def undo_state():
    history = load_history()
    if not history:
        return None
    state = history.pop()
    tasks = {int(k): v for k, v in state["tasks"].items()}
    save_history(history)
    return {"tasks": tasks, "next_id": state["next_id"]}


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = str(task["id"]) + " [" + status + "] " + task["title"]
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join("#" + t for t in task["tags"])
    if task["due"]:
        line += " due:" + task["due"]
    return line


def cmd_add(args):
    if not args:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Error: --priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: " + priority, file=sys.stderr)
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
                print("Error: --due requires a value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                date.fromisoformat(due_str)
            except ValueError:
                print("Invalid date: " + due_str, file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    # Save state BEFORE mutation
    append_history(tasks, next_id)
    task_id = next_id
    tasks[task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_tasks(tasks, next_id + 1)
    print("Added " + str(task_id))


def cmd_list(args):
    tasks, _ = load_tasks()
    if not tasks:
        print("No tasks")
        return

    sort_mode = None
    filter_tag = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
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
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1

    task_list = sorted(tasks.values(), key=lambda t: t["id"])

    if filter_tag:
        task_list = [t for t in task_list if filter_tag in t["tags"]]

    if overdue:
        today_str = today_arg if today_arg else date.today().isoformat()
        try:
            today_date = date.fromisoformat(today_str)
        except ValueError:
            print("Invalid date: " + today_str, file=sys.stderr)
            sys.exit(1)
        task_list = [t for t in task_list if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today_date]

    if sort_mode == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        task_list.sort(key=lambda t: (order.get(t["priority"], 1), t["id"]))

    if not task_list:
        print("No tasks")
        return

    for t in task_list:
        print(format_task_line(t))


def cmd_done(args):
    if not args:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: invalid task id: " + args[0], file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)

    append_history(tasks, next_id)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print("Done " + str(task_id))


def cmd_delete(args):
    if not args:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: invalid task id: " + args[0], file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)

    append_history(tasks, next_id)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print("Deleted " + str(task_id))


def cmd_edit(args):
    if not args:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: invalid task id: " + args[0], file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)

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
        print("Error: --title required", file=sys.stderr)
        sys.exit(1)

    append_history(tasks, next_id)
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited " + str(task_id))


def cmd_search(args):
    if not args:
        print("Error: missing search text", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks.values() if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task_line(t))


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
        print("Error: --format required", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()
    task_list = sorted(tasks.values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in task_list:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in task_list:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(str(t["id"]) + "," + t["title"] + "," + done_str + "," + t["priority"] + "," + tags_str + "," + due_str)
    else:
        print("Error: unknown format: " + fmt, file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total_count = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total_count))


def cmd_undo(args):
    state = undo_state()
    if state is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    save_tasks(state["tasks"], state["next_id"])
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
        print("Unknown
