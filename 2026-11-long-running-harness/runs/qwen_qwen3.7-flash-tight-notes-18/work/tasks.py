#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load data from tasks.json or return initial state."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1, "history": []}


def save_data(data):
    """Save data to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def snapshot(data):
    """Create a snapshot for undo (deep copy of tasks and next_id)."""
    return {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }


def push_history(data):
    """Push current state onto history stack."""
    data["history"].append(snapshot(data))


def pop_history(data):
    """Pop last state from history and restore."""
    if not data["history"]:
        return False
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    return True


def format_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def err(msg):
    """Print error message to stderr and exit 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def parse_add_args(args):
    """Parse arguments for add command."""
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                err("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                err(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                err("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                err("--due requires a value")
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                err(f"Invalid date: {due}")
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        err("add requires a title")
    title = " ".join(title_parts)
    return title, priority, tags, due


def parse_list_args(args):
    """Parse arguments for list command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                err("--sort requires a value")
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                err(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                err("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                err("--today requires a value")
            today_str = args[i + 1]
            i += 2
        else:
            err(f"Unknown argument: {args[i]}")
    return sort_priority, tag_filter, overdue, today_str


def parse_edit_args(args):
    """Parse arguments for edit command."""
    new_title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                err("--title requires a value")
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
            break
        else:
            err(f"Unknown argument: {args[i]}")
    if not new_title_parts:
        err("--title requires a value")
    return " ".join(new_title_parts)


def cmd_add(args):
    """Handle the add command."""
    title, priority, tags, due = parse_add_args(args)
    data = load_data()
    push_history(data)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the list command."""
    data = load_data()
    sort_priority, tag_filter, overdue, today_str = parse_list_args(args)

    tasks = data["tasks"]

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue
    if overdue:
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and t["due"] < today.strftime("%Y-%m-%d")
        ]

    # Sort by priority if requested
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(format_task_line(t))


def cmd_done(args):
    """Handle the done command."""
    if not args:
        err("done requires an ID")
    task_id = int(args[0])
    data = load_data()
    found = False
    for t in data["tasks"]:
        if t["id"] == task_id:
            push_history(data)
            t["done"] = True
            save_data(data)
            print(f"Done {task_id}")
            found = True
            break
    if not found:
        err(f"No such task: {task_id}")


def cmd_delete(args):
    """Handle the delete command."""
    if not args:
        err("delete requires an ID")
    task_id = int(args[0])
    data = load_data()
    found = False
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            push_history(data)
            data["tasks"].pop(i)
            save_data(data)
            print(f"Deleted {task_id}")
            found = True
            break
    if not found:
        err(f"No such task: {task_id}")


def cmd_edit(args):
    """Handle the edit command."""
    if not args:
        err("edit requires an ID")
    task_id = int(args[0])
    new_title = parse_edit_args(args[1:])
    data = load_data()
    found = False
    for t in data["tasks"]:
        if t["id"] == task_id:
            push_history(data)
            t["title"] = new_title
            save_data(data)
            print(f"Edited {task_id}")
            found = True
            break
    if not found:
        err(f"No such task: {task_id}")


def cmd_search(args):
    """Handle the search command."""
    if not args:
        err("search requires TEXT")
    query = " ".join(args).lower()
    data = load_data()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task_line(t))


def cmd_export(args):
    """Handle the export command."""
    if not args or args[0] != "--format":
        err("export requires --format json|csv")
    fmt = args[1] if len(args) > 1 else ""
    if fmt not in ("json", "csv"):
        err(f"Unknown format: {fmt}")
    data = load_data()
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
                "due": t.get("due", None),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority','medium')},{tags_str},{due_str}")


def cmd_stats(args):
    """Handle the stats command."""
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle the undo command."""
    data = load_data()
    if not data["history"]:
        err("Nothing to undo")
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        err("Usage: python3 tasks.py <command> [args]")
    command = sys.argv[1]
    args = sys.argv[2:]
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
        err(f"Unknown command: {command}")
    commands[command](args)


if __name__ == "__main__":
    main()
