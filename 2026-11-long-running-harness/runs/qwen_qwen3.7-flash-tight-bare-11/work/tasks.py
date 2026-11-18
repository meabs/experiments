#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    """Load tasks from JSON file, return (tasks_dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = {int(k): v for k, v in data["tasks"].items()}
    return tasks, data["next_id"]


def save_tasks(tasks, next_id):
    """Save tasks to JSON file."""
    str_tasks = {str(k): v for k, v in tasks.items()}
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": str_tasks, "next_id": next_id}, f, indent=2)


def load_history():
    """Load undo history."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Save undo history."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(state):
    """Push current state onto undo history."""
    history = load_history()
    history.append(state)
    save_history(history)


def pop_history():
    """Pop the most recent state from undo history."""
    history = load_history()
    if not history:
        error("Nothing to undo")
    state = history.pop()
    save_history(history)
    return state


def error(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # medium shows no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        parts.extend(["#" + t for t in tags])
    # Due date suffix
    due = task.get("due")
    if due:
        parts.append("due:" + due)
    return " ".join(parts)


# --- Command implementations ---

def cmd_add(args):
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
                error(f"Invalid priority: {priority}")
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
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    tasks, next_id = load_tasks()

    # Save state for undo
    push_history({"tasks": tasks, "next_id": next_id})

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

    print(f"Added {task_id}")


def cmd_list(args):
    sort_mode = None
    tag_filter = None
    overdue = False
    today_arg = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing today value")
            today_arg = args[i + 1]
            try:
                datetime.strptime(today_arg, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {today_arg}")
            i += 2
        else:
            i += 1

    if today_arg is None:
        today = date.today().isoformat()
    else:
        today = today_arg

    tasks, _ = load_tasks()
    filtered = list(tasks.values())

    if tag_filter is not None:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    if overdue:
        filtered = [t for t in filtered
                    if not t["done"] and t.get("due") and t["due"] < today]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
    else:
        for task in filtered:
            print(format_task_line(task))


def cmd_done(args):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")
    tasks, next_id = load_tasks()

    task = tasks.get(task_id)
    if task is None:
        error(f"No such task: {task_id}")

    push_history({"tasks": tasks, "next_id": next_id})
    task["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        error("Missing task ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    tasks, next_id = load_tasks()

    task = tasks.get(task_id)
    if task is None:
        error(f"No such task: {task_id}")

    push_history({"tasks": tasks, "next_id": next_id})
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        error("Missing task ID")
    
    # First arg must be the task ID
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task ID: {args[0]}")

    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title value")
            i += 1
            # Collect remaining args as the new title
            title_parts = args[i:]
            break
        else:
            i += 1

    if not title_parts:
        error("Missing new title")

    tasks, next_id = load_tasks()

    task = tasks.get(task_id)
    if task is None:
        error(f"No such task: {task_id}")

    push_history({"tasks": tasks, "next_id": next_id})
    task["title"] = " ".join(title_parts)
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks.values() if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args):
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
        error("Missing --format argument")

    tasks, _ = load_tasks()
    sorted_tasks = sorted(tasks.values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in sorted_tasks:
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
        for task in sorted_tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{done_str},{task.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    state = pop_history()
    save_tasks(state["tasks"], state["next_id"])
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
        error("Usage: tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
