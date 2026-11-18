#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks data from JSON file, or return empty state."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def print_task(task):
    """Print a task line in the standard format."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f'{task["id"]} {status} {task["title"]}']
    # priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # tags suffix
    if task.get("tags"):
        parts.extend(f"#{t}" for t in task["tags"])
    # due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    print(" ".join(parts))


def cmd_add(args):
    """Add a new task."""
    data = load_data()

    # Parse flags
    priority = "medium"
    i = 0
    while i < len(args):
        if args[i] == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    # Title is everything except recognized flags
    # We need to reconstruct title by removing --priority VALUE segments
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority" and i + 1 < len(args):
            # Skip this flag and its value
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": [],
        "due": None,
    }
    # Save snapshot before mutation for undo
    data["undo_history"].append({
        "tasks": [t.copy() for t in data["tasks"]],
        "next_id": data["next_id"],
    })
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f'Added {task["id"]}')


def cmd_list(args):
    """List tasks, optionally filtered/sorted."""
    data = load_data()
    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return
    # Parse optional flags
    sort_by = None
    filter_tag = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        else:
            i += 1

    filtered = tasks
    if filter_tag is not None:
        filtered = [t for t in filtered if filter_tag in t.get("tags", [])]

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for task in filtered:
        print_task(task)


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    if not args:
        print("Usage: tasks.py done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    # Find the task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save snapshot before mutation for undo
    data["undo_history"].append({
        "tasks": [t.copy() for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task["done"] = True
    save_data(data)
    print(f'Done {task_id}')


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    if not args:
        print("Usage: tasks.py delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    # Find the task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Save snapshot before mutation for undo
    data["undo_history"].append({
        "tasks": [t.copy() for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f'Deleted {task_id}')


def cmd_edit(args):
    """Edit a task's title."""
    data = load_data()
    if not args:
        print("Usage: tasks.py edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    # Find the task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Parse --title flag
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            # Collect all remaining args as the new title
            new_title = " ".join(args[i + 1:])
            break
        i += 1

    if new_title is None:
        print("Usage: tasks.py edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    # Save snapshot before mutation for undo
    data["undo_history"].append({
        "tasks": [t.copy() for t in data["tasks"]],
        "next_id": data["next_id"],
    })

    task["title"] = new_title
    save_data(data)
    print(f'Edited {task_id}')


def cmd_search(args):
    """Search tasks by title substring."""
    data = load_data()
    if not args:
        print("Usage: tasks.py search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print_task(task)


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
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
        print("Usage: tasks.py export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Print task statistics."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = data["undo_history"].pop()
    data["tasks"] = previous["tasks"]
    data["next_id"] = previous["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "add":
        cmd_add(args)
    elif command == "list":
        cmd_list(args)
    elif command == "done":
        cmd_done(args)
    elif command == "delete":
        cmd_delete(args)
    elif command == "edit":
        cmd_edit(args)
    elif command == "search":
        cmd_search(args)
    elif command == "export":
        cmd_export(args)
    elif command == "stats":
        cmd_stats(args)
    elif command == "undo":
        cmd_undo(args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
