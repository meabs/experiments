#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"


def load_data():
    """Load task data from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    tasks = {}
    for k, v in raw.get("tasks", {}).items():
        tid = int(k)
        v["id"] = tid
        tasks[tid] = v
    next_id = int(raw.get("next_id", 1))
    history = raw.get("history", [])
    return {"tasks": tasks, "next_id": next_id, "history": history}


def save_data(data):
    """Save task data to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def make_task(title, done=False, priority="medium", tags=None, due=None):
    """Create a new task dict."""
    return {
        "title": title,
        "done": done,
        "priority": priority,
        "tags": tags if tags is not None else [],
        "due": due,
    }


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    for tag in task["tags"]:
        line += " #{}".format(tag)
    if task["due"]:
        line += " due:{}".format(task["due"])
    return line


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def snapshot(data):
    """Create a deep copy of tasks and next_id for undo history."""
    return {
        "old_tasks": copy.deepcopy(data["tasks"]),
        "old_next_id": data["next_id"],
    }


def do_add(data, args):
    """Handle the 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            i += 1
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: {}".format(priority))
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            i += 1
            tags.append(args[i])
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            i += 1
            due = args[i]
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, OverflowError):
                error("Invalid date: {}".format(due))
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Missing title")

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["next_id"] += 1

    snap = snapshot(data)
    data["history"].append({"command": "add", "snap": snap})

    data["tasks"][task_id] = make_task(title, priority=priority, tags=tags, due=due)
    save_data(data)
    print("Added {}".format(task_id))


def do_list(data, args):
    """Handle the 'list' command."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            i += 1
            if args[i] == "priority":
                sort_priority = True
            else:
                error("Unknown sort option: {}".format(args[i]))
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            i += 1
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            i += 1
            today_str = args[i]
        else:
            error("Unknown option: {}".format(arg))
        i += 1

    if today_str:
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error("Invalid date: {}".format(today_str))
    else:
        today = date.today()

    tasks = list(data["tasks"].values())

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today.isoformat()]

    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def do_done(data, args):
    """Handle the 'done' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task ID: {}".format(args[0]))

    if task_id not in data["tasks"]:
        error("No such task: {}".format(task_id))

    snap = snapshot(data)
    data["history"].append({"command": "done", "snap": snap, "task_id": task_id})

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def do_delete(data, args):
    """Handle the 'delete' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task ID: {}".format(args[0]))

    if task_id not in data["tasks"]:
        error("No such task: {}".format(task_id))

    snap = snapshot(data)
    data["history"].append({"command": "delete", "snap": snap, "task_id": task_id})

    del data["tasks"][task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def do_edit(data, args):
    """Handle the 'edit' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("Invalid task ID: {}".format(args[0]))

    if task_id not in data["tasks"]:
        error("No such task: {}".format(task_id))

    new_title = None
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            i += 1
            title_parts = [args[i]]
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        else:
            error("Unknown option: {}".format(arg))
        i += 1

    if new_title is None:
        error("Missing --title")

    snap = snapshot(data)
    data["history"].append({"command": "edit", "snap": snap, "task_id": task_id})

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def do_search(data, args):
    """Handle the 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    matches = []
    for t in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def do_export(data, args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            i += 1
            fmt = args[i]
        else:
            error("Unknown option: {}".format(arg))
        i += 1

    if fmt is None:
        error("Missing --format")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
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
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(output.getvalue().rstrip("\n"))
    else:
        error("Unknown format: {}".format(fmt))


def do_stats(data, args):
    """Handle the 'stats' command."""
    open_count = sum(1 for t in data["tasks"].values() if not t["done"])
    done_count = sum(1 for t in data["tasks"].values() if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def do_undo(data, args):
    """Handle the 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")

    entry = data["history"].pop()
    data["tasks"] = entry["snap"]["old_tasks"]
    data["next_id"] = entry["snap"]["old_next_id"]
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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    if command not in COMMANDS:
        error("Unknown command: {}".format(command))

    data = load_data()
    COMMANDS[command](data, sys.argv[2:])


if __name__ == "__main__":
    main()
