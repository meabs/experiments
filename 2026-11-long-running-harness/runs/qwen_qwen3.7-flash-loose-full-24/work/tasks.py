#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    # Priority suffix
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


def cmd_add(args):
    """Add a new task."""
    data = load_data()
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
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
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("add requires a title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    # Save state before mutation for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    data["tasks"].append(task)
    data["next_id"] = task_id + 1
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """List tasks."""
    data = load_data()
    tasks = data["tasks"]

    # Parse options
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            if sort_by not in ("priority",):
                print(f"Invalid sort option: {sort_by}", file=sys.stderr)
                sys.exit(1)
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
            today_str = args[i + 1]
            i += 1
        else:
            i += 1

    # Filter by tag
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter
    if overdue:
        today = today_str if today_str else date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort by priority
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    if not args:
        print("done requires an ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    # Save state before mutation for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    if not args:
        print("delete requires an ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    # Save state before mutation for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Edit a task's title."""
    data = load_data()
    if not args:
        print("edit requires an ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    # Find --title flag
    new_title_parts = []
    i = 1
    found_title = False
    while i < len(args):
        if args[i] == "--title":
            i += 1
            found_title = True
            while i < len(args) and not args[i].startswith("--"):
                new_title_parts.append(args[i])
                i += 1
        else:
            i += 1

    if not found_title or not new_title_parts:
        print("edit requires --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(new_title_parts)
    # Save state before mutation for undo
    data["history"].append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Search tasks by text in title."""
    data = load_data()
    if not args:
        print("search requires TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Invalid format: {fmt}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    if fmt is None:
        print("--format is required", file=sys.stderr)
        sys.exit(1)

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
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    """Print stats about tasks."""
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
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
