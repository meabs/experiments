#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import datetime


DATA_FILE = "tasks.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"next_id": 1, "tasks": [], "history": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    done_mark = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], done_mark, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join("#" + t for t in task["tags"])
    if task.get("due"):
        line += " due:" + task["due"]
    return line


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(priority))
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: {}".format(due))
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    title = " ".join(title_parts)
    data = load_data()
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] = task_id + 1
    data["history"].append({"op": "add", "task_id": task_id})
    save_data(data)
    print("Added {}".format(task_id))


def cmd_list(args):
    sort_by = None
    tag_filter = None
    overdue_today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue_today = True
            today_str = None
            i += 1
            while i < len(args):
                if args[i] == "--today":
                    if i + 1 >= len(args):
                        error("--today requires a value")
                    today_str = args[i + 1]
                    i += 2
                else:
                    break
            if today_str is None:
                today_str = datetime.now().strftime("%Y-%m-%d")
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: {}".format(today_str))
            data = load_data()
            tasks = [t for t in data["tasks"] if not t["done"] and t.get("due") and t["due"] < today_str]
            if not tasks:
                print("No tasks")
                return
            for t in tasks:
                print(task_line(t))
            return
        else:
            i += 1

    data = load_data()
    tasks = list(data["tasks"])

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if sort_by == "priority":
        porder = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))
    data = load_data()
    task = find_task(data, task_id)
    if task is None:
        error("No such task: {}".format(task_id))
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))
    data = load_data()
    task = find_task(data, task_id)
    if task is None:
        error("No such task: {}".format(task_id))
    task_data = {
        "id": task["id"],
        "title": task["title"],
        "done": task["done"],
        "priority": task["priority"],
        "tags": list(task["tags"]),
        "due": task.get("due"),
    }
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    data["history"].append({"op": "delete", "task": task_data})
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task id: {}".format(args[0]))
    title_index = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_index = i
            break
    if title_index is None or title_index + 1 >= len(args):
        error("Usage: edit ID --title NEW TITLE")
    new_title = " ".join(args[title_index + 1:])
    data = load_data()
    task = find_task(data, task_id)
    if task is None:
        error("No such task: {}".format(task_id))
    old_title = task["title"]
    task["title"] = new_title
    data["history"].append({"op": "edit", "task_id": task_id, "old_title": old_title})
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")
    query = " ".join(args).lower()
    data = load_data()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt is None:
        error("Usage: export --format json|csv")
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                tags_str, due_str))
    else:
        error("Invalid format: {}".format(fmt))


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
        error("Nothing to undo")
    last_op = data["history"].pop()
    if last_op["op"] == "add":
        task_id = last_op["task_id"]
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        data["next_id"] = task_id
    elif last_op["op"] == "delete":
        task_data = last_op["task"]
        data["tasks"].append(task_data)
        if task_data["id"] >= data["next_id"]:
            data["next_id"] = task_data["id"] + 1
    elif last_op["op"] == "edit":
        task_id = last_op["task_id"]
        old_title = last_op["old_title"]
        task = find_task(data, task_id)
        if task:
            task["title"] = old_title
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
        error("Usage: python3 tasks.py <command> [args]")
    cmd_name = sys.argv[1]
    if cmd_name not in COMMANDS:
        error("Unknown command: {}".format(cmd_name))
    COMMANDS[cmd_name](sys.argv[2:])


if __name__ == "__main__":
    main()
