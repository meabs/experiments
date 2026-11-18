#!/usr/bin/env python3
"""Command-line task manager using only Python 3 standard library."""

import sys
import json
import os
import copy
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix (high/low only, medium has no suffix)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def validate_date(date_str):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args, data):
    """Handle the 'add' command."""
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
                error("Invalid date: ")
            due = args[i + 1]
            if not validate_date(due):
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    
    title = " ".join(title_parts)
    if not title:
        error("Missing task title")
    
    tid = data["next_id"]
    data["next_id"] += 1
    
    task = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][str(tid)] = task
    
    # Record for undo
    data["undo_stack"].append({
        "type": "add",
        "task": copy.deepcopy(task),
        "next_id_before": tid,
    })
    
    save_data(data)
    print(f"Added {tid}")


def cmd_list(args, data):
    """Handle the 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
            if i < len(args) and args[i] == "--today" and i + 1 < len(args):
                today_str = args[i + 1]
                i += 2
            elif i < len(args) and args[i].startswith("--"):
                pass
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    
    tasks = list(data["tasks"].values())
    
    # Filter by tag
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    
    # Filter overdue
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]
    
    # Sort
    if sort_priority:
        order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    
    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args, data):
    """Handle the 'done' command."""
    if not args:
        error("Usage: done ID")
    try:
        tid = args[0]
    except ValueError:
        error(f"No such task: {args[0]}")
    
    if tid not in data["tasks"]:
        error(f"No such task: {tid}")
    
    data["tasks"][tid]["done"] = True
    
    # Record for undo
    data["undo_stack"].append({
        "type": "done",
        "task_id": tid,
        "done_before": False,
    })
    
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Handle the 'delete' command."""
    if not args:
        error("Usage: delete ID")
    try:
        tid = args[0]
    except ValueError:
        error(f"No such task: {args[0]}")
    
    if tid not in data["tasks"]:
        error(f"No such task: {tid}")
    
    deleted_task = data["tasks"].pop(tid)
    
    # Record for undo
    data["undo_stack"].append({
        "type": "delete",
        "task": copy.deepcopy(deleted_task),
        "next_id_before": data["next_id"],
    })
    
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Handle the 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    
    try:
        tid = args[0]
    except ValueError:
        error(f"No such task: {args[0]}")
    
    if tid not in data["tasks"]:
        error(f"No such task: {tid}")
    
    # Find --title and everything after it
    title_idx = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_idx = i
            break
    
    if title_idx is None or title_idx + 1 >= len(args):
        error("Usage: edit ID --title NEW TITLE")
    
    new_title = " ".join(args[title_idx + 1:])
    
    old_task = data["tasks"][tid]
    
    # Record for undo
    data["undo_stack"].append({
        "type": "edit",
        "task_id": tid,
        "old_title": old_task["title"],
    })
    
    data["tasks"][tid]["title"] = new_title
    
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Handle the 'search' command."""
    if not args:
        error("Usage: search TEXT")
    
    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]
    
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args, data):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    
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
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Handle the 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Handle the 'undo' command."""
    if not data["undo_stack"]:
        error("Nothing to undo")
    
    entry = data["undo_stack"].pop()
    
    if entry["type"] == "add":
        tid = entry["task"]["id"]
        data["tasks"].pop(str(tid), None)
        data["next_id"] = entry["next_id_before"]
    elif entry["type"] == "done":
        tid = entry["task_id"]
        if tid in data["tasks"]:
            data["tasks"][tid]["done"] = entry["done_before"]
    elif entry["type"] == "delete":
        task = entry["task"]
        data["tasks"][str(task["id"])] = task
        data["next_id"] = entry["next_id_before"]
    elif entry["type"] == "edit":
        tid = entry["task_id"]
        if tid in data["tasks"]:
            data["tasks"][tid]["title"] = entry["old_title"]
    
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        error("Usage: python3 tasks.py <command> [args]")
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    data = load_data()
    
    commands = {
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
    
    if command not in commands:
        error(f"Unknown command: {command}")
    
    commands[command](args, data)


if __name__ == "__main__":
    main()
