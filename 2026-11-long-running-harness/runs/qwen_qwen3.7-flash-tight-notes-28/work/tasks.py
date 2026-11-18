#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    """Load tasks from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "next_id": 1}


def save_tasks(data):
    """Save tasks to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    """Load undo history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    """Save undo history."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(data):
    """Push current state onto history stack before a mutating command."""
    history = load_history()
    history.append(json.dumps(data))
    # Keep only last 1000 states to avoid unbounded growth
    if len(history) > 1000:
        history = history[-1000:]
    save_history(history)


def undo():
    """Undo the most recent mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = json.loads(history.pop())
    save_history(history)
    save_tasks(previous_state)
    print("Undone")


def validate_date(date_str):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_task_line(task):
    """Format a task for display."""
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium priority shows no suffix
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle the 'add' command."""
    data = load_tasks()
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
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i]
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
        else:
            title_parts.append(arg)
        i += 1

    title = " ".join(title_parts)
    if not title:
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    push_history(data)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_tasks(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle the 'list' command."""
    data = load_tasks()
    if not data["tasks"]:
        print("No tasks")
        return

    sort_by = None
    filter_tag = None
    overdue_mode = False
    today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i]
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue_mode = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                print("Missing today date", file=sys.stderr)
                sys.exit(1)
            today = args[i]
        i += 1

    if overdue_mode:
        if today is None:
            today = date.today().isoformat()
        if not validate_date(today):
            print(f"Invalid date: {today}", file=sys.stderr)
            sys.exit(1)
        today_dt = datetime.strptime(today, "%Y-%m-%d").date()
        filtered = [
            t for t in data["tasks"]
            if not t["done"] and t.get("due") and datetime.strptime(t["due"], "%Y-%m-%d").date() < today_dt
        ]
    elif filter_tag:
        filtered = [t for t in data["tasks"] if filter_tag in t.get("tags", [])]
    else:
        filtered = list(data["tasks"])

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    data = load_tasks()
    for task in data["tasks"]:
        if task["id"] == task_id:
            push_history(data)
            task["done"] = True
            save_tasks(data)
            print(f"Done {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    data = load_tasks()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            push_history(data)
            data["tasks"].pop(i)
            save_tasks(data)
            print(f"Deleted {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    """Handle the 'edit' command."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
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
        i += 1

    if new_title is None:
        print("Missing --title flag", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    for task in data["tasks"]:
        if task["id"] == task_id:
            push_history(data)
            task["title"] = new_title
            save_tasks(data)
            print(f"Edited {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    data = load_tasks()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle the 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i]
        i += 1

    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Handle the 'stats' command."""
    data = load_tasks()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

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
        "undo": lambda _: undo(),
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args)


if __name__ == "__main__":
    main()
