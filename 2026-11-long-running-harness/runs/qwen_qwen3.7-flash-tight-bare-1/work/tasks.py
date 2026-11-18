#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and state from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and state to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    # priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # tags suffix
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def parse_add_args(args):
    """Parse add command arguments."""
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("Missing title")
    return " ".join(title_parts), priority, tags, due


def cmd_add(args, data):
    """Handle 'add' command."""
    title, priority, tags, due = parse_add_args(args)
    if priority is None:
        priority = "medium"
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    str_id = str(task_id)
    data["tasks"][str_id] = task
    data["next_id"] = task_id + 1
    # Save state before mutating for undo
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing value for --sort")
            if args[i + 1] != "priority":
                error(f"Unknown sort option: {args[i + 1]}")
            sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing value for --today")
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today_str}")
            i += 2
        else:
            error(f"Unknown argument: {args[i]}")

    tasks = list(data["tasks"].values())

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    # Overdue filter
    if overdue:
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
            today_str_normalized = today.strftime("%Y-%m-%d")
        else:
            today = date.today()
            today_str_normalized = today.strftime("%Y-%m-%d")
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_str_normalized]

    # Sort
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        if not overdue and not tag_filter:
            print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    str_id = str(task_id)
    if str_id not in data["tasks"]:
        error(f"No such task: {task_id}")
    data["tasks"][str_id]["done"] = True
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    str_id = str(task_id)
    if str_id not in data["tasks"]:
        error(f"No such task: {task_id}")
    del data["tasks"][str_id]
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")
    str_id = str(task_id)
    if str_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing value for --title")
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is not None:
        data["tasks"][str_id]["title"] = new_title
        data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
        save_data(data)
        print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")
    text = " ".join(args).lower()
    tasks = [t for t in data["tasks"].values() if text in t["title"].lower()]
    tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No matches")
        return
    for t in tasks:
        print(task_line(t))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing value for --format")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Missing --format")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    open_count = sum(1 for t in data["tasks"].values() if not t["done"])
    done_count = sum(1 for t in data["tasks"].values() if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        error("Nothing to undo")
    prev_state = json.loads(data["history"].pop())
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
        error(f"Unknown command: {command}")

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
