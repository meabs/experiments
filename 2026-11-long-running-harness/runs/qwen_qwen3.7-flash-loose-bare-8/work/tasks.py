#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load data from tasks.json, creating default if needed."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        for key in ("tasks", "next_id", "history"):
            if key not in data:
                if key == "tasks":
                    data[key] = {}
                elif key == "history":
                    data[key] = []
                else:
                    data[key] = 1
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "history": []}


def save_data(data):
    """Save data to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def _key(task_id):
    return str(task_id)


def format_task(task):
    """Format a task for display."""
    status = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], status, task["title"])
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    if task.get("tags"):
        line += " " + " ".join("#" + t for t in task["tags"])
    # Due date suffix
    if task.get("due"):
        line += " due:" + task["due"]
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def snapshot(data):
    """Create a snapshot of mutable state for undo."""
    return {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }


def cmd_add(args, data):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error("Invalid priority: " + priority)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error("Invalid date: " + due)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("Missing task title")
    title = " ".join(title_parts)

    prev_state = snapshot(data)

    task_id = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["history"].append(prev_state)
    data["tasks"][str(task_id)] = task
    save_data(data)
    print("Added " + str(task_id))


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing date value")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    tasks = list(data["tasks"].values())

    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error("Invalid date: " + today_str)
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
        ]

    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(format_task(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    key = str(task_id)
    if key not in data["tasks"]:
        error("No such task: " + str(task_id))

    prev_state = snapshot(data)

    data["tasks"][key]["done"] = True
    data["history"].append(prev_state)
    save_data(data)
    print("Done " + str(task_id))


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    key = str(task_id)
    if key not in data["tasks"]:
        error("No such task: " + str(task_id))

    prev_state = snapshot(data)

    del data["tasks"][key]
    data["history"].append(prev_state)
    save_data(data)
    print("Deleted " + str(task_id))


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error("No such task: " + args[0])
    key = str(task_id)
    if key not in data["tasks"]:
        error("No such task: " + str(task_id))

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            title_parts = []
            j = i + 1
            while j < len(args):
                if args[j].startswith("--"):
                    break
                title_parts.append(args[j])
                j += 1
            if not title_parts:
                error("Missing title value")
            new_title = " ".join(title_parts)
            break
        i += 1

    if new_title is None:
        error("Missing --title flag")

    prev_state = snapshot(data)

    data["tasks"][key]["title"] = new_title
    data["history"].append(prev_state)
    save_data(data)
    print("Edited " + str(task_id))


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")
    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task(t))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format flag")
    if fmt not in ("json", "csv"):
        error("Invalid format: " + fmt)

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

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
        print(json.dumps(export_data))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                tags_str,
                due_str,
            ])
        print(output.getvalue().rstrip("\r\n"))


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total))


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")
    prev_state = data["history"].pop()
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
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

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error("Unknown command: " + command)

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
