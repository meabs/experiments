#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import json
import os
import sys
from datetime import datetime, date

DATA_FILE = "tasks.json"
UNDO_FILE = "undo_state.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = {int(k): v for k, v in data["tasks"].items()}
        return tasks, data.get("next_id", 1)
    return {}, 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo_state(tasks, next_id):
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_undo_history(history)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def err(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def do_add(args):
    if not args:
        err("Missing task title")
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                err("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                err("Invalid priority: {}".format(priority))
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                err("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                err("Missing due date value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                err("Invalid date: {}".format(due))
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        err("Missing task title")
    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    push_undo_state(tasks, next_id)
    task_id = next_id
    tasks[task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    next_id += 1
    save_tasks(tasks, next_id)
    print("Added {}".format(task_id))


def do_list(args):
    tasks, next_id = load_tasks()
    if not tasks:
        print("No tasks")
        return
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort_priority = True
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
        filtered = {}
        for tid, task in tasks.items():
            if tag_filter in task.get("tags", []):
                filtered[tid] = task
        tasks = filtered
    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                err("Invalid date: {}".format(today_str))
        else:
            today = date.today()
        filtered = {}
        for tid, task in tasks.items():
            if task["done"]:
                continue
            if task.get("due"):
                try:
                    due_date = datetime.strptime(task["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered[tid] = task
                except ValueError:
                    pass
        tasks = filtered
    if not tasks:
        print("No tasks")
        return
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_ids = sorted(tasks.keys(), key=lambda tid: (priority_order.get(tasks[tid].get("priority", "medium"), 1), tid))
    else:
        sorted_ids = sorted(tasks.keys())
    for tid in sorted_ids:
        print(task_line(tasks[tid]))


def do_done(args):
    if not args:
        err("Missing task id")
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        err("No such task: {}".format(task_id))
    push_undo_state(tasks, next_id)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print("Done {}".format(task_id))


def do_delete(args):
    if not args:
        err("Missing task id")
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        err("No such task: {}".format(task_id))
    push_undo_state(tasks, next_id)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print("Deleted {}".format(task_id))


def do_edit(args):
    if not args:
        err("Missing edit arguments")
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        err("No such task: {}".format(task_id))
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                err("Missing title value")
            new_title = " ".join(args[i + 1:])
            break
        i += 1
    if new_title is None:
        err("Missing --title")
    push_undo_state(tasks, next_id)
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited {}".format(task_id))


def do_search(args):
    if not args:
        err("Missing search text")
    text = " ".join(args)
    tasks, next_id = load_tasks()
    matched = {}
    for tid, task in tasks.items():
        if text.lower() in task["title"].lower():
            matched[tid] = task
    if not matched:
        print("No matches")
        return
    for tid in sorted(matched.keys()):
        print(task_line(matched[tid]))


def do_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt is None:
        err("Missing --format")
    if fmt not in ("json", "csv"):
        err("Invalid format: {}".format(fmt))
    tasks, next_id = load_tasks()
    sorted_ids = sorted(tasks.keys())
    if fmt == "json":
        output = []
        for tid in sorted_ids:
            task = tasks[tid]
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due", None),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for tid in sorted_ids:
            task = tasks[tid]
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due", "")
            print("{},{},{},{},{},{}".format(tid, task["title"], done_str, task.get("priority", "medium"), tags_str, due_str))


def do_stats(args):
    tasks, next_id = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def do_undo(args):
    history = load_undo_history()
    if not history:
        err("Nothing to undo")
    prev_state = history.pop()
    save_tasks(prev_state["tasks"], prev_state["next_id"])
    save_undo_history(history)
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
        err("Usage: python3 tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        err("Unknown command: {}".format(command))
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
