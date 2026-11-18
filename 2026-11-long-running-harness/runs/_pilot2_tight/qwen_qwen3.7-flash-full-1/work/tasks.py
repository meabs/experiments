#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and state from the data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and state to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    """Add a new task."""
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1

    if title is None:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    # Validate date if provided
    if due is not None:
        import datetime
        try:
            datetime.date.fromisoformat(due)
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    next_id = data["next_id"]
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][next_id] = task
    data["next_id"] = next_id + 1

    # Record undo state
    data["undo_stack"].append({
        "type": "add",
        "task_id": next_id,
        "prev_next_id": next_id,
    })
    save_data(data)
    print(f"Added {next_id}")


def cmd_list(args, data):
    """List tasks."""
    sort_by = None
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing value for --today", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if today is None:
        import datetime
        today = datetime.date.today().isoformat()

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    prev_state = dict(data["tasks"][task_id])
    data["tasks"][task_id]["done"] = True
    data["undo_stack"].append({
        "type": "done",
        "task_id": task_id,
        "prev_state": prev_state,
    })
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task = data["tasks"].pop(task_id)
    data["undo_stack"].append({
        "type": "delete",
        "task_id": task_id,
        "task": task,
        "prev_next_id": data["next_id"],
    })
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    """Edit a task's title."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            break
        i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    prev_state = dict(data["tasks"][task_id])
    data["tasks"][task_id]["title"] = new_title
    data["undo_stack"].append({
        "type": "edit",
        "task_id": task_id,
        "prev_state": prev_state,
    })
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    """Search tasks by title substring."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args, data):
    """Export tasks in JSON or CSV format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing value for --format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
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
            print(f'{t["id"]},{t["title"]},{done_str},{t["priority"]},{tags_str},{due_str}')
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Print task statistics."""
    open_count = sum(1 for t in data["tasks"].values() if not t["done"])
    done_count = sum(1 for t in data["tasks"].values() if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating operation."""
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    action = data["undo_stack"].pop()
    if action["type"] == "add":
        del data["tasks"][action["task_id"]]
        data["next_id"] = action["prev_next_id"]
    elif action["type"] == "done":
        data["tasks"][action["task_id"]] = action["prev_state"]
    elif action["type"] == "delete":
        data["tasks"][action["task_id"]] = action["task"]
        data["next_id"] = action["prev_next_id"]
    elif action["type"] == "edit":
        data["tasks"][action["task_id"]] = action["prev_state"]
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

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
