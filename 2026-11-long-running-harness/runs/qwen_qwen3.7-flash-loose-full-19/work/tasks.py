#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    """Load tasks from tasks.json, or return empty list if file doesn't exist."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    """Save tasks to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_history():
    """Load undo history from history.json."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history):
    """Save undo history to history.json."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def next_id(tasks):
    """Compute the next available id (never reuse deleted ids)."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def record_mutation(tasks):
    """Record current state onto undo history after a mutation."""
    history = load_history()
    history.append(json.dumps(tasks))
    # Limit history to avoid unbounded growth
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def undo():
    """Undo the last mutating command."""
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = json.loads(history.pop())
    save_history(history)
    save_tasks(previous_state)
    print("Undone")


def format_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]

    # Priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")

    # Tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        parts.append("#" + tag)

    # Due date suffix
    due = task.get("due")
    if due:
        parts.append("due:" + due)

    return " ".join(parts)


def cmd_add(args):
    """Handle the 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: " + priority, file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except ValueError:
                print("Invalid date: " + due, file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks = load_tasks()
    task_id = next_id(tasks)
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print("Added " + str(task_id))


def cmd_list(args):
    """Handle the 'list' command."""
    sort_option = None
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_option = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = load_tasks()

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter: only open tasks whose due date is before today
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    # Sort
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    """Handle the 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks)
            record_mutation(tasks)
            print("Done " + str(task_id))
            return
    print("No such task: " + str(task_id), file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Handle the 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    tasks = load_tasks()
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            save_tasks(tasks)
            record_mutation(tasks)
            print("Deleted " + str(task_id))
            return
    print("No such task: " + str(task_id), file=sys.stderr)
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
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            save_tasks(tasks)
            record_mutation(tasks)
            print("Edited " + str(task_id))
            return
    print("No such task: " + str(task_id), file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Handle the 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if text in t["title"].lower()]
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
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

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
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            lines.append(str(t["id"]) + "," + t["title"] + "," + done_str + "," + t.get("priority", "medium") + "," + tags_str + "," + due_str)
        print("\n".join(lines))
    else:
        print("Invalid format: " + fmt, file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Handle the 'stats' command."""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total_count))


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "undo":
        undo()
    elif command in COMMANDS:
        COMMANDS[command](args)
    else:
        print("Unknown command: " + command, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
