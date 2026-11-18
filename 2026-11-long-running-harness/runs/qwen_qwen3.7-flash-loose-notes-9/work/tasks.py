#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
import copy
from datetime import date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "history": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    # Ensure next_id exists for backwards compatibility
    if "next_id" not in data:
        if data["tasks"]:
            data["next_id"] = max(t["id"] for t in data["tasks"]) + 1
        else:
            data["next_id"] = 1
    return data


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    done_mark = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_mark} {task['title']}"
    # Priority suffix (medium shows no suffix)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    """Print error message to stderr and exit."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def cmd_add(args):
    """Handle 'add' command."""
    if not args:
        error("Missing title")

    data = load_data()
    title_parts = []
    priority = None
    tags = []
    due = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing priority value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing due date value")
            due = args[i + 1]
            # Validate date
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError()
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
            except (ValueError, OverflowError):
                error(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(arg)
            i += 1

    title = " ".join(title_parts)
    if not title:
        error("Missing title")

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["next_id"] += 1

    # Save snapshot for undo
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = list(data["tasks"])

    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value")
            filter_tag = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("Missing date value")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filter: show only open tasks whose due date is before --today
    if overdue:
        today = today_str if today_str else date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        error("Missing task id")

    data = load_data()
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save snapshot for undo
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Missing task id")

    data = load_data()
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    # Save snapshot for undo
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Missing task id")

    data = load_data()
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")

    rest_args = args[1:]

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        error(f"No such task: {task_id}")

    new_title = None
    i = 0
    while i < len(rest_args):
        if rest_args[i] == "--title":
            if i + 1 >= len(rest_args):
                error("Missing title value")
            # Collect all remaining words as title
            new_title = " ".join(rest_args[i + 1:])
            break
        i += 1

    if new_title is None:
        error("Missing --title")

    # Save snapshot for undo
    data["history"].append(copy.deepcopy({"tasks": data["tasks"], "next_id": data["next_id"]}))
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    data = load_data()
    query = " ".join(args).lower()

    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()

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
        error("Missing --format")

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_val = t.get("due")
            due_str = due_val if due_val else ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()

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
    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
