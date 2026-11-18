#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from JSON file. Return (tasks dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", {})
        # Ensure all keys are strings
        tasks = {str(k): v for k, v in tasks.items()}
        return tasks, data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return {}, 1


def save_data(tasks, next_id):
    """Save tasks data to JSON file."""
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def format_task_line(tid, task):
    """Format a single task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"

    if task.get("priority"):
        p = task["priority"]
        if p == "high":
            line += " (high)"
        elif p == "low":
            line += " (low)"
        # medium shows no suffix

    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)

    if task.get("due"):
        line += f" due:{task['due']}"

    return line


def add_task(args, tasks, next_id):
    """Handle 'add' command."""
    if len(args) == 0:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    # Parse options
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due" and i + 1 < len(args):
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    task_id = str(next_id)
    tasks[task_id] = {
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    next_id += 1
    save_data(tasks, next_id)
    print(f"Added {task_id}")


def list_tasks(args, tasks, next_id):
    """Handle 'list' command."""
    sort_key = None
    tag_filter = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_key = args[i + 1]
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

    if today_str is None:
        today_str = date.today().isoformat()

    if not tasks:
        print("No tasks")
        return

    # Build sorted list by id
    result = sorted(tasks.items(), key=lambda x: int(x[0]))

    if overdue:
        today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        result = [
            (tid, t) for tid, t in result
            if not t["done"]
            and t["due"] is not None
            and datetime.strptime(t["due"], "%Y-%m-%d").date() < today_date
        ]

    if tag_filter:
        result = [(tid, t) for tid, t in result if tag_filter in t.get("tags", [])]

    if sort_key == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2, None: 3}
        result = sorted(result, key=lambda x: (priority_order.get(x[1].get("priority"), 3), int(x[0])))

    for tid, t in result:
        print(format_task_line(tid, t))


def done_task(args, tasks, next_id):
    """Handle 'done' command."""
    if len(args) == 0:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = str(int(args[0]))
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    tasks[task_id]["done"] = True
    save_data(tasks, next_id)
    print(f"Done {task_id}")


def delete_task(args, tasks, next_id):
    """Handle 'delete' command."""
    if len(args) == 0:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = str(int(args[0]))
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    del tasks[task_id]
    save_data(tasks, next_id)
    print(f"Deleted {task_id}")


def edit_task(args, tasks, next_id):
    """Handle 'edit' command."""
    if len(args) == 0:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = str(int(args[0]))
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    idx = 1
    new_title_parts = []
    collecting_title = False

    while idx < len(args):
        if args[idx] == "--title":
            collecting_title = True
            idx += 1
        elif collecting_title:
            new_title_parts.append(args[idx])
            idx += 1
        else:
            idx += 1

    if not new_title_parts:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    tasks[task_id]["title"] = " ".join(new_title_parts)
    save_data(tasks, next_id)
    print(f"Edited {task_id}")


def search_tasks(args, tasks, next_id):
    """Handle 'search' command."""
    if len(args) == 0:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    results = []

    for tid in sorted(tasks.keys(), key=int):
        if query in tasks[tid]["title"].lower():
            results.append((tid, tasks[tid]))

    if not results:
        print("No matches")
        return

    for tid, t in results:
        print(format_task_line(tid, t))


def export_tasks(args, tasks, next_id):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)

    items = sorted(tasks.items(), key=lambda x: int(x[0]))

    if fmt == "json":
        out = []
        for tid, t in items:
            out.append({
                "id": int(tid),
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(out))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for tid, t in items:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            pri = t.get("priority") or ""
            print(f"{tid},{t['title']},{done_str},{pri},{tags_str},{due_str}")


def stats_tasks(args, tasks, next_id):
    """Handle 'stats' command."""
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": add_task,
    "list": list_tasks,
    "done": done_task,
    "delete": delete_task,
    "edit": edit_task,
    "search": search_tasks,
    "export": export_tasks,
    "stats": stats_tasks,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_data()
    COMMANDS[command](args, tasks, next_id)


if __name__ == "__main__":
    main()
