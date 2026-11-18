#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    """Save tasks to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def format_task_line(task):
    """Format a task for display."""
    check = "x" if task["done"] else " "
    line = '{} [{}] {}'.format(task["id"], check, task["title"])
    return line


def cmd_add(args, data):
    """Add a new task."""
    title = " ".join(args)
    if not title:
        print("Error: no title provided", file=sys.stderr)
        sys.exit(1)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": "medium",
        "tags": [],
        "due": None,
    }

    # Save undo state
    data["undo_history"].append({
        "type": "add",
        "task": task,
        "next_id": data["next_id"],
    })

    data["tasks"].append(task)
    data["next_id"] += 1
    save_tasks(data)
    print("Added {}".format(task["id"]))


def cmd_list(args, data):
    """List all tasks."""
    sort_priority = False
    tag_filter = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        else:
            i += 1

    tasks = list(data["tasks"])

    # Apply tag filter
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Sort by priority order
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args, data):
    """Mark a task as done."""
    try:
        task_id = int(args[0])
    except (ValueError, IndexError):
        print("Error: please provide a task ID", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    # Save undo state
    data["undo_history"].append({
        "type": "done",
        "task": dict(task),
        "next_id": data["next_id"],
    })

    task["done"] = True
    save_tasks(data)
    print("Done {}".format(task_id))


def cmd_delete(args, data):
    """Delete a task."""
    try:
        task_id = int(args[0])
    except (ValueError, IndexError):
        print("Error: please provide a task ID", file=sys.stderr)
        sys.exit(1)

    task = None
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            task = t
            del data["tasks"][i]
            break

    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    # Save undo state
    data["undo_history"].append({
        "type": "delete",
        "task": task,
        "next_id": data["next_id"],
    })

    save_tasks(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args, data):
    """Edit a task title."""
    try:
        task_id = int(args[0])
    except (ValueError, IndexError):
        print("Error: please provide a task ID", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    # Parse --title flag
    new_title_parts = []
    if "--title" in args[1:]:
        title_idx = args.index("--title")
        new_title_parts = args[title_idx + 1:]

    new_title = " ".join(new_title_parts)
    if not new_title:
        print("Error: no new title provided", file=sys.stderr)
        sys.exit(1)

    # Save undo state
    data["undo_history"].append({
        "type": "edit",
        "task": dict(task),
        "old_title": task["title"],
        "next_id": data["next_id"],
    })

    task["title"] = new_title
    save_tasks(data)
    print("Edited {}".format(task_id))


def cmd_search(args, data):
    """Search tasks by title."""
    text = " ".join(args).lower()
    if not text:
        print("Error: search text required", file=sys.stderr)
        sys.exit(1)

    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args, data):
    """Export tasks in json or csv format."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Error: --format required (json or csv)", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data))

    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            done_str = "true" if t["done"] else "false"
            row = "{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str)
            print(row)

    else:
        print("Error: unknown format '{}'".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Print stats about tasks."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args, data):
    """Undo the last mutating operation."""
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    entry = data["undo_history"].pop()
    op_type = entry["type"]

    if op_type == "add":
        # Remove the added task
        task_id = entry["task"]["id"]
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        data["next_id"] = entry["next_id"]

    elif op_type == "done":
        # Restore the task's done state
        for t in data["tasks"]:
            if t["id"] == entry["task"]["id"]:
                t["done"] = entry["task"]["done"]
                break
        data["next_id"] = entry["next_id"]

    elif op_type == "delete":
        # Restore the deleted task
        data["tasks"].append(entry["task"])
        data["next_id"] = entry["next_id"]

    elif op_type == "edit":
        # Restore the old title
        for t in data["tasks"]:
            if t["id"] == entry["task"]["id"]:
                t["title"] = entry["old_title"]
                break
        data["next_id"] = entry["next_id"]

    save_tasks(data)
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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
