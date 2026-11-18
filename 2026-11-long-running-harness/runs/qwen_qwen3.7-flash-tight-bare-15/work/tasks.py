#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
import copy
from datetime import date

DATA_FILE = "tasks.json"


def load_data():
    """Load data from tasks.json, creating default structure if needed."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        for key in ("tasks", "next_id", "undo_stack"):
            if key not in data:
                data[key] = [] if key != "next_id" else 1
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "next_id": 1, "undo_stack": []}


def save_data(data):
    """Save data to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def parse_args(args):
    """Parse command-line arguments into positional args and flags."""
    result = {"_args": [], "_flags": {}}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            multi_keys = ("tag", "title", "today", "format", "priority", "sort", "due")
            if key in multi_keys:
                if i + 1 >= len(args):
                    error(f"--{key} requires a value")
                val = args[i + 1]
                if key not in result["_flags"]:
                    result["_flags"][key] = []
                result["_flags"][key].append(val)
                i += 2
            else:
                result["_flags"][key] = True
                i += 1
        else:
            result["_args"].append(arg)
            i += 1
    return result


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string. Returns the string if valid, None otherwise."""
    try:
        parts = date_str.split("-")
        if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
            return None
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
        return date_str
    except (ValueError, IndexError):
        return None


def push_undo(data):
    """Push current state onto the undo stack."""
    data["undo_stack"].append({
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"]
    })
    if len(data["undo_stack"]) > 50:
        data["undo_stack"] = data["undo_stack"][-50:]


def cmd_add(data, parsed):
    """Handle the 'add' command."""
    args = parsed["_args"]
    flags = parsed["_flags"]
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = " ".join(args)
    prio = flags.get("priority", ["medium"])[0]
    if prio not in ("high", "medium", "low"):
        error(f"Invalid priority: {prio}")
    due = None
    if "due" in flags:
        due = validate_date(flags["due"][0])
        if due is None:
            error(f"Invalid date: {flags['due'][0]}")
    tags = flags.get("tag", [])
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": prio,
        "tags": tags,
        "due": due
    }
    push_undo(data)
    data["tasks"].append(task)
    data["next_id"] = task_id + 1
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(data, parsed):
    """Handle the 'list' command."""
    flags = parsed["_flags"]
    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return
    filtered = list(tasks)
    if "tag" in flags:
        tag_filter = flags["tag"]
        filtered = [t for t in filtered if any(tag in t.get("tags", []) for tag in tag_filter)]
    if "overdue" in flags:
        today_str = flags.get("today", [date.today().isoformat()])[0]
        today_date = validate_date(today_str)
        if today_date is None:
            error(f"Invalid date: {today_str}")
        today_d = date.fromisoformat(today_date)
        filtered = [t for t in filtered if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today_d]
    if flags.get("sort", []) == ["priority"]:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])
    if not filtered:
        print("No tasks")
        return
    for task in filtered:
        print(task_line(task))


def cmd_done(data, parsed):
    """Handle the 'done' command."""
    args = parsed["_args"]
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")
    push_undo(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(data, parsed):
    """Handle the 'delete' command."""
    args = parsed["_args"]
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")
    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(data, parsed):
    """Handle the 'edit' command."""
    args = parsed["_args"]
    flags = parsed["_flags"]
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid ID: {args[0]}")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error(f"No such task: {task_id}")
    if "title" not in flags:
        error("Usage: edit ID --title NEW TITLE")
    new_title = " ".join(flags["title"])
    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(data, parsed):
    """Handle the 'search' command."""
    args = parsed["_args"]
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args).lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(task_line(task))


def cmd_export(data, parsed):
    """Handle the 'export' command."""
    flags = parsed["_flags"]
    if "format" not in flags:
        error("Usage: export --format json|csv")
    fmt = flags["format"][0]
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
                "due": t.get("due")
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(data, parsed):
    """Handle the 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(data, parsed):
    """Handle the 'undo' command."""
    if not data["undo_stack"]:
        error("Nothing to undo")
    prev = data["undo_stack"].pop()
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
    args = sys.argv[1:]
    if not args:
        error("Usage: python3 tasks.py <command> [args]")
    command = args[0]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    parsed = parse_args(args[1:])
    data = load_data()
    COMMANDS[command](data, parsed)


if __name__ == "__main__":
    main()
