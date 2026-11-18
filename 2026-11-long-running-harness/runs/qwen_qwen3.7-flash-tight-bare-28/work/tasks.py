#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.getcwd(), "tasks.json")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # Priority suffix
    p = task.get("priority", "medium")
    if p == "high":
        line += " (high)"
    elif p == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f' due:{task["due"]}'
    return line


def parse_args(argv):
    if len(argv) < 2:
        return None, {}
    command = argv[1]
    args = argv[2:]
    options = {
        "priority": "medium",
        "tags": [],
        "due": None,
        "sort": None,
        "tag_filter": None,
        "overdue": False,
        "today": None,
        "format": None,
        "new_title": None,
        "title": None,
    }
    i = 0
    title_parts = []
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            options["priority"] = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            options["tags"].append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            options["due"] = args[i + 1]
            i += 2
        elif arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            options["sort"] = args[i + 1]
            i += 2
        elif arg == "--tag-filter":
            if i + 1 >= len(args):
                error("--tag-filter requires a value")
            options["tag_filter"] = args[i + 1]
            i += 2
        elif arg == "--overdue":
            options["overdue"] = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            options["today"] = args[i + 1]
            i += 2
        elif arg == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            options["format"] = args[i + 1]
            i += 2
        elif arg == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            options["new_title"] = args[i + 1]
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    if title_parts:
        options["title"] = " ".join(title_parts)
    return command, options


def cmd_add(data, opts):
    title = opts.get("title")
    if not title:
        error("add requires a title")
    priority = opts.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")
    due = opts.get("due")
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            error(f"Invalid date: {due}")
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": list(opts.get("tags", [])),
        "due": due,
    }
    # Save snapshot before mutation
    data["history"].append({"tasks": list(data["tasks"]), "next_id": data["next_id"]})
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(data, opts):
    tasks = list(data["tasks"])
    tag_filter = opts.get("tag_filter")
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if opts.get("overdue"):
        today_str = opts.get("today", date.today().isoformat())
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    sort_opt = opts.get("sort")
    if sort_opt == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    elif sort_opt is None:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        if not opts.get("overdue") and not tag_filter:
            print("No tasks")
        return
    for task in tasks:
        print(task_line(task))


def cmd_done(data, opts):
    val = opts.get("title")
    if not val:
        error("done requires an ID")
    try:
        task_id = int(val)
    except ValueError:
        error(f"Invalid ID: {val}")
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if not task:
        error(f"No such task: {task_id}")
    data["history"].append({"tasks": list(data["tasks"]), "next_id": data["next_id"]})
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(data, opts):
    val = opts.get("title")
    if not val:
        error("delete requires an ID")
    try:
        task_id = int(val)
    except ValueError:
        error(f"Invalid ID: {val}")
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if not task:
        error(f"No such task: {task_id}")
    data["history"].append({"tasks": list(data["tasks"]), "next_id": data["next_id"]})
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(data, opts):
    val = opts.get("title")
    if not val:
        error("edit requires an ID")
    try:
        task_id = int(val)
    except ValueError:
        error(f"Invalid ID: {val}")
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if not task:
        error(f"No such task: {task_id}")
    new_title = opts.get("new_title")
    if not new_title:
        error("edit --title requires a new title")
    data["history"].append({"tasks": list(data["tasks"]), "next_id": data["next_id"]})
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(data, opts):
    text = opts.get("title")
    if not text:
        error("search requires search text")
    results = [t for t in data["tasks"] if text.lower() in t["title"].lower()]
    if not results:
        print("No matches")
        return
    results.sort(key=lambda t: t["id"])
    for task in results:
        print(task_line(task))


def cmd_export(data, opts):
    fmt = opts.get("format")
    if not fmt:
        error("export requires --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        export_list = []
        for t in tasks:
            export_list.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_list))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            writer.writerow([t["id"], t["title"], done_str, t.get("priority", "medium"), tags_str, due_str])
        print(output.getvalue(), end="")


def cmd_stats(data, opts):
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(data, opts):
    if not data["history"]:
        error("Nothing to undo")
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
    command, opts = parse_args(sys.argv)
    if not command:
        error("Usage: python3 tasks.py <command> [args]")
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    data = load_data()
    COMMANDS[command](data, opts)


if __name__ == "__main__":
    main()
