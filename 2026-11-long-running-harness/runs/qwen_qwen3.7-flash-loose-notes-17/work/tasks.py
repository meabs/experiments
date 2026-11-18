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
HISTORY_FILE = "tasks_history.json"


def load_data():
    """Load tasks from tasks.json, returning (tasks_dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        # Convert string keys back to int
        tasks = {int(k): v for k, v in data.get("tasks", {}).items()}
        return tasks, int(data.get("next_id", 1))
    except (json.JSONDecodeError, KeyError):
        return {}, 1


def save_data(tasks, next_id):
    """Save tasks to tasks.json."""
    # Convert int keys to strings for JSON
    str_tasks = {str(k): v for k, v in tasks.items()}
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": str_tasks, "next_id": next_id}, f)


def load_history():
    """Load undo history from tasks_history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_history(history):
    """Save undo history to tasks_history.json."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    """Push current state onto undo history."""
    history = load_history()
    history.append({"tasks": copy.deepcopy(tasks), "next_id": next_id})
    # Limit history size to avoid unbounded growth
    if len(history) > 1000:
        history = history[-1000:]
    save_history(history)


def pop_history():
    """Pop state from undo history. Returns (tasks, next_id) or None."""
    history = load_history()
    if not history:
        return None
    state = history.pop()
    save_history(history)
    return state["tasks"], state["next_id"]


def parse_add_args(args):
    """Parse arguments for 'add' command."""
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
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    if not title_parts:
        error("Missing task title")
    return " ".join(title_parts), priority, tags, due


def parse_edit_args(args):
    """Parse arguments for 'edit' command."""
    new_title_parts = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
            break
        else:
            error(f"Unknown argument: {arg}")
    if not new_title_parts:
        error("Missing new title after --title")
    return " ".join(new_title_parts)


def format_task_line(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    # Tags suffix
    if task["tags"]:
        tag_suffix = " ".join(f"#{t}" for t in task["tags"])
        line += f" {tag_suffix}"
    # Due date suffix
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle 'add' command."""
    title, priority, tags, due = parse_add_args(args)
    tasks, next_id = load_data()
    push_history(tasks, next_id)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks[next_id] = task
    save_data(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    """Handle 'list' command."""
    tasks, _ = load_data()
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif arg == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")

    if today_str is None:
        today = date.today().isoformat()
    else:
        today = today_str

    task_list = list(tasks.values())

    # Filter by tag
    if filter_tag is not None:
        task_list = [t for t in task_list if filter_tag in t["tags"]]

    # Filter overdue
    if overdue:
        today_date = date.fromisoformat(today)
        task_list = [
            t for t in task_list
            if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today_date
        ]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        task_list.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        task_list.sort(key=lambda t: t["id"])

    if not task_list:
        print("No tasks")
    else:
        for task in task_list:
            print(format_task_line(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    tasks, next_id = load_data()
    if task_id not in tasks:
        error(f"No such task: {task_id}")
    push_history(tasks, next_id)
    tasks[task_id]["done"] = True
    save_data(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    tasks, next_id = load_data()
    if task_id not in tasks:
        error(f"No such task: {task_id}")
    push_history(tasks, next_id)
    del tasks[task_id]
    save_data(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Missing task ID")
    task_id = int(args[0])
    tasks, next_id = load_data()
    if task_id not in tasks:
        error(f"No such task: {task_id}")
    new_title = parse_edit_args(args[1:])
    push_history(tasks, next_id)
    tasks[task_id]["title"] = new_title
    save_data(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")
    text = " ".join(args).lower()
    tasks, _ = load_data()
    matches = [t for t in tasks.values() if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if fmt is None:
        error("Missing --format option")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks, _ = load_data()
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
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in task_list:
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(output.getvalue(), end="")


def cmd_stats(args):
    """Handle 'stats' command."""
    tasks, _ = load_data()
    total = len(tasks)
    done_count = sum(1 for t in tasks.values() if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    result = pop_history()
    if result is None:
        error("Nothing to undo")
    tasks, next_id = result
    save_data(tasks, next_id)
    print("Undone")


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


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
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
