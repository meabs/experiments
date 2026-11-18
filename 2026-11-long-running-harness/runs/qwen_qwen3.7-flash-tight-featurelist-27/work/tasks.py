#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"

VALID_PRIORITIES = {"high", "medium", "low"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def load_tasks():
    """Load tasks from the JSON file, or return empty state if it doesn't exist."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(state):
    """Save tasks to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(state, f)


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = args[0]

    if command == "add":
        cmd_add(args[1:])
    elif command == "list":
        cmd_list(args[1:])
    elif command == "done":
        cmd_done(args[1:])
    elif command == "delete":
        cmd_delete(args[1:])
    elif command == "edit":
        cmd_edit(args[1:])
    elif command == "search":
        cmd_search(args[1:])
    elif command == "export":
        cmd_export(args[1:])
    elif command == "stats":
        cmd_stats()
    elif command == "undo":
        cmd_undo()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


def cmd_add(args):
    """Handle 'add TITLE' command."""
    if not args:
        print("Usage: tasks.py add TITLE [--priority high|medium|low]", file=sys.stderr)
        sys.exit(1)

    # Parse --priority flag
    priority = "medium"
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in VALID_PRIORITIES:
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    state = load_tasks()
    task_id = state["next_id"]
    state["tasks"].append({
        "id": task_id,
        "title": " ".join(title_parts),
        "done": False,
        "priority": priority,
        "tags": [],
        "due": None
    })
    state["next_id"] = task_id + 1
    save_tasks(state)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle 'list' command."""
    state = load_tasks()
    tasks = state["tasks"]

    # Parse flags
    sort_by_priority = False
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_val = args[i + 1]
            if sort_val == "priority":
                sort_by_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue
    if overdue:
        from datetime import date
        if today:
            today_date = date.fromisoformat(today)
        else:
            today_date = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and
                 date.fromisoformat(t["due"]) < today_date]

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if sort_by_priority:
        tasks = sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    for task in tasks:
        line = format_task_line(task)
        print(line)


def format_task_line(task):
    """Format a task into its display line."""
    status = "[x]" if task["done"] else "[ ]"
    suffixes = ""
    # Priority suffix (feature 5)
    if task.get("priority") == "high":
        suffixes += " (high)"
    elif task.get("priority") == "low":
        suffixes += " (low)"
    # Tags suffix (feature 6)
    if task.get("tags"):
        tag_suffix = " " + " ".join(f"#{t}" for t in task["tags"])
        suffixes += tag_suffix
    # Due date suffix (feature 7)
    if task.get("due"):
        suffixes += f" due:{task['due']}"
    return f"{task['id']} {status} {task['title']}{suffixes}"


def cmd_done(args):
    """Handle 'done ID' command."""
    if not args:
        print("Usage: tasks.py done ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    state = load_tasks()
    for task in state["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(state)
            print(f"Done {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Handle 'delete ID' command."""
    if not args:
        print("Usage: tasks.py delete ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    state = load_tasks()
    for i, task in enumerate(state["tasks"]):
        if task["id"] == task_id:
            state["tasks"].pop(i)
            save_tasks(state)
            print(f"Deleted {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    """Handle 'edit ID --title NEW TITLE' command."""
    if not args:
        print("Usage: tasks.py edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    # Parse --title flag
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            # Collect all remaining args as the new title
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        print("Usage: tasks.py edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    state = load_tasks()
    for task in state["tasks"]:
        if task["id"] == task_id:
            task["title"] = new_title
            save_tasks(state)
            print(f"Edited {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Handle 'search TEXT' command."""
    if not args:
        print("Usage: tasks.py search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    state = load_tasks()

    matches = [t for t in state["tasks"] if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    """Handle 'export --format json|csv' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            break
        i += 1

    if not fmt or fmt not in ("json", "csv"):
        print("Usage: tasks.py export --format json|csv", file=sys.stderr)
        sys.exit(1)

    state = load_tasks()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due")
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            lines.append(f"{task['id']},{task['title']},{str(task['done']).lower()},{task.get('priority', 'medium')},{tags_str},{due_str}")
        print("\n".join(lines))


def cmd_stats():
    """Handle 'stats' command."""
    state = load_tasks()
    tasks = state["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo():
    """Handle 'undo' command."""
    print("Nothing to undo", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
