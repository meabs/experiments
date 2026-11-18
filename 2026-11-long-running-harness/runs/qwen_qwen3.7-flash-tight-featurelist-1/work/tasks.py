#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    """Load tasks from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, KeyError):
        return {"tasks": {}, "next_id": 1}


def save_data(data):
    """Save tasks to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    """Load undo history from tasks_history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return []


def save_history(history):
    """Save undo history to tasks_history.json."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(data):
    """Push current data onto undo history."""
    history = load_history()
    history.append({"tasks": data["tasks"], "next_id": data["next_id"]})
    save_history(history)


def undo():
    """Undo the most recent mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = history.pop()
    data = {"tasks": prev["tasks"], "next_id": prev["next_id"]}
    save_data(data)
    save_history(history)
    print("Undone")


def format_task(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # priority suffix (feature 5)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # tags suffix (feature 6)
    if task.get("tags"):
        line += " " + " ".join(f"#{tag}" for tag in task["tags"])
    # due date suffix (feature 7)
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_data()
    
    title_parts = []
    priority = "medium"
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    
    title = " ".join(title_parts)
    if not title:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    
    task_id = data["next_id"]
    task = {
        "title": title,
        "done": False,
        "priority": priority,
        "tags": [],
        "due": None,
    }
    data["tasks"][task_id] = task
    data["next_id"] += 1
    
    push_history(data)
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_data()
    tasks = list(data["tasks"].values())
    
    if not tasks:
        print("No tasks")
        return
    
    # Filter by tag (feature 6)
    tag_filter = None
    sort_mode = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--sort" and i + 1 < len(args):
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            i += 2
        else:
            i += 1
    
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    
    if overdue:
        from datetime import datetime, date
        if today is None:
            today_str = date.today().isoformat()
        else:
            today_str = today
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        tasks = [
            t for t in tasks
            if not t["done"]
            and t.get("due")
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today_date
        ]
    
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    
    if not tasks:
        print("No tasks")
        return
    
    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Handle the 'done' command."""
    data = load_data()
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    
    data["tasks"][task_id]["done"] = True
    push_history(data)
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle the 'delete' command."""
    data = load_data()
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    
    del data["tasks"][task_id]
    push_history(data)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle the 'edit' command."""
    data = load_data()
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title after --title", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1
    
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    
    data["tasks"][task_id]["title"] = new_title
    push_history(data)
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle the 'search' command."""
    data = load_data()
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()
    
    tasks = [t for t in data["tasks"].values() if search_text in t["title"].lower()]
    tasks.sort(key=lambda t: t["id"])
    
    if not tasks:
        print("No matches")
        return
    
    for task in tasks:
        print(format_task(task))


def cmd_export(args):
    """Handle the 'export' command."""
    data = load_data()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    
    if fmt == "json":
        result = []
        for task in tasks:
            result.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            done_str = "true" if task["done"] else "false"
            print(f'{task["id"]},{task["title"]},{done_str},{task.get("priority","medium")},{tags_str},{due_str}')
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_data()
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": lambda args: undo(),
}


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
