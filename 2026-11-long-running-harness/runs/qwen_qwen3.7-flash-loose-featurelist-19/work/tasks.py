#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
import datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    # Ensure all task ids are stored as strings (JSON keys are always strings)
    new_tasks = {}
    for k, v in data.get("tasks", {}).items():
        new_tasks[str(k)] = v
    data["tasks"] = new_tasks
    return data


def save_data(data):
    """Save tasks and undo history to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    suffixes = []
    priority = task.get("priority", "medium")
    if priority == "high":
        suffixes.append("(high)")
    elif priority == "low":
        suffixes.append("(low)")
    tags = task.get("tags", [])
    for tag in tags:
        suffixes.append(f"#{tag}")
    due = task.get("due")
    if due:
        suffixes.append(f"due:{due}")
    return f"{task['id']} {status} {task['title']}" + (
        " " + " ".join(suffixes) if suffixes else ""
    )


def parse_add_args(args):
    """Parse arguments for add command. Returns (title, priority, tags, due)."""
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("--priority requires a value")
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("--due requires a value")
            due = args[i]
            # Validate date
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                datetime.date(year, month, day)
            except (ValueError, OverflowError):
                error(f"Invalid date: {due}")
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        error("Missing task title")

    return " ".join(title_parts), priority, tags, due


def cmd_add(args, data):
    """Handle the 'add' command."""
    title, priority, tags, due = parse_add_args(args)

    task_id = str(data["next_id"])

    # Save undo state BEFORE mutation
    old_state = json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]})

    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["next_id"] = int(task_id) + 1

    data["history"].append(old_state)

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    """Handle the 'list' command."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort" and i + 1 < len(args):
            i += 1
            if args[i] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i]}")
        elif arg == "--tag" and i + 1 < len(args):
            i += 1
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today" and i + 1 < len(args):
            i += 1
            today_str = args[i]
        i += 1

    tasks = list(data["tasks"].values())

    # Filter by tag if specified
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue tasks
    if overdue:
        if today_str:
            today = datetime.date.fromisoformat(today_str)
        else:
            today = datetime.date.today()
        tasks = [
            t for t in tasks
            if not t["done"]
            and t.get("due")
            and datetime.date.fromisoformat(t["due"]) < today
        ]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), int(t["id"])))
    else:
        tasks.sort(key=lambda t: int(t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Handle the 'done' command."""
    if not args:
        error("Usage: done ID")
    task_id = args[0]
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save undo state BEFORE mutation
    old_state = json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]})

    data["tasks"][task_id]["done"] = True
    data["history"].append(old_state)
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Handle the 'delete' command."""
    if not args:
        error("Usage: delete ID")
    task_id = args[0]
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    # Save undo state BEFORE mutation
    old_state = json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]})

    del data["tasks"][task_id]
    data["history"].append(old_state)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Handle the 'edit' command."""
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    task_id = args[0]
    if task_id not in data["tasks"]:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if not new_title:
        error("Missing --title")

    # Save undo state BEFORE mutation
    old_state = json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]})

    data["tasks"][task_id]["title"] = new_title
    data["history"].append(old_state)
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Handle the 'search' command."""
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args).lower()
    matches = [t for t in data["tasks"].values() if text in t["title"].lower()]
    matches.sort(key=lambda t: int(t["id"]))
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            i += 1
            fmt = args[i]
        i += 1

    if not fmt:
        error("--format required")

    tasks = sorted(data["tasks"].values(), key=lambda t: int(t["id"]))

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": int(t["id"]),
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        error(f"Unknown format: {fmt}")


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
    if not data["history"]:
        error("Nothing to undo")
    previous_state = json.loads(data["history"].pop())
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
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

    data = load_data()
    args = sys.argv[2:]
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
