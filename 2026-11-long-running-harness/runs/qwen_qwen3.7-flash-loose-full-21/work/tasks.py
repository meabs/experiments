#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    # Convert string keys back to integers
    tasks = {}
    for k, v in data["tasks"].items():
        tasks[int(k)] = v
    data["tasks"] = tasks
    return data


def save_data(data):
    """Save tasks data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    """Format a task for display in list/search output."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix (medium has no suffix)
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        line += f" #{tag}"
    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


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
                error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due_val = args[i + 1]
            try:
                datetime.strptime(due_val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due_val}")
            due = due_val
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        error("No title provided")

    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] += 1

    # Record undo state
    data["undo_history"].append({
        "type": "add",
        "task_id": task_id,
    })

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue (only open tasks)
    if overdue:
        today_date = datetime.strptime(today_str, "%Y-%m-%d").date() if today_str else date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_date.strftime("%Y-%m-%d")]

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args or not args[0].isdigit():
        error("Usage: done ID")
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")
    data["tasks"][task_id]["done"] = True
    data["undo_history"].append({
        "type": "done",
        "task_id": task_id,
    })
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args or not args[0].isdigit():
        error("Usage: delete ID")
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")
    deleted_task = data["tasks"].pop(task_id)
    data["undo_history"].append({
        "type": "delete",
        "task_id": task_id,
        "task_data": deleted_task,
    })
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args or not args[0].isdigit():
        error("Usage: edit ID --title NEW TITLE")
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            while i < len(args) and args[i] != "--title":
                new_title_parts.append(args[i])
                i += 1
        else:
            i += 1

    new_title = " ".join(new_title_parts)
    if not new_title:
        error("No new title provided")

    old_title = data["tasks"][task_id]["title"]
    data["tasks"][task_id]["title"] = new_title
    data["undo_history"].append({
        "type": "edit",
        "task_id": task_id,
        "old_title": old_title,
    })
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        print("No matches")
        return
    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        error("Usage: export --format json|csv")

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            done_str = "true" if task["done"] else "false"
            print(f"{task['id']},{task['title']},{done_str},{task.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["undo_history"]:
        error("Nothing to undo")

    entry = data["undo_history"].pop()
    if entry["type"] == "add":
        task_id = entry["task_id"]
        if task_id in data["tasks"]:
            del data["tasks"][task_id]
        # Restore next_id to be what it was before this add
        data["next_id"] = max(1, task_id)
    elif entry["type"] == "done":
        task_id = entry["task_id"]
        if task_id in data["tasks"]:
            data["tasks"][task_id]["done"] = False
    elif entry["type"] == "delete":
        task_id = entry["task_id"]
        # Restore the deleted task
        if "task_data" in entry:
            data["tasks"][task_id] = entry["task_data"]
        data["next_id"] = max(data["next_id"], task_id + 1)
    elif entry["type"] == "edit":
        task_id = entry["task_id"]
        if task_id in data["tasks"]:
            data["tasks"][task_id]["title"] = entry["old_title"]

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
