#!/usr/bin/env python3
"""A command-line task manager using only Python 3 standard library."""

import json
import os
import sys
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_undo_snapshot(data):
    """Push current state onto the undo stack (deep copy)."""
    snapshot = {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }
    data["history"].append(snapshot)


def cmd_add(args, data):
    """Handle 'add' command."""
    title, priority, tags, due = _parse_add_args(args)

    # Validate priority
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        return 1

    # Validate due date
    if due is not None:
        if not validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            return 1

    # Save undo snapshot before mutation
    save_undo_snapshot(data)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": list(tags),
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")
    return 0


def _parse_add_args(args):
    """Parse add-specific arguments. Returns (title, priority, tags, due)."""
    positional = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--priority":
            i += 1
            if i < len(args):
                priority = args[i]
        elif a == "--tag":
            i += 1
            if i < len(args):
                tags.append(args[i])
        elif a == "--due":
            i += 1
            if i < len(args):
                due = args[i]
        else:
            positional.append(a)
        i += 1
    if not positional:
        print("Error: add requires a TITLE", file=sys.stderr)
        return ("", "medium", [], None)
    return (" ".join(positional), priority, tags, due)


def task_line(task):
    """Build the display line for a task."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    p = task.get("priority", "medium")
    if p == "high":
        line += " (high)"
    elif p == "low":
        line += " (low)"
    tags = task.get("tags", [])
    for tag in tags:
        line += f" #{tag}"
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def validate_date(d):
    """Check if a string is a valid YYYY-MM-DD date."""
    try:
        datetime.strptime(d, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_list(args, data):
    """Handle 'list' command."""
    opts = _parse_list_args(args)
    tasks = list(data["tasks"])

    # Filter by tag
    if opts["tag_filter"] is not None:
        tasks = [t for t in tasks if opts["tag_filter"] in t.get("tags", [])]

    # Overdue filter
    if opts["overdue"]:
        today_str = opts["today"] or date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]

    if not tasks:
        print("No tasks")
        return 0

    # Sort
    if opts["sort"] == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for t in tasks:
        print(task_line(t))
    return 0


def _parse_list_args(args):
    """Parse list-specific arguments."""
    result = {"tag_filter": None, "overdue": False, "today": None, "sort": None}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--tag":
            i += 1
            if i < len(args):
                result["tag_filter"] = args[i]
        elif a == "--overdue":
            result["overdue"] = True
        elif a == "--today":
            i += 1
            if i < len(args):
                result["today"] = args[i]
        elif a == "--sort":
            i += 1
            if i < len(args):
                result["sort"] = args[i]
        i += 1
    return result


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args or not args[0].isdigit():
        print("Error: done requires an ID", file=sys.stderr)
        return 1
    task_id = int(args[0])
    task = _find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1
    save_undo_snapshot(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")
    return 0


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args or not args[0].isdigit():
        print("Error: delete requires an ID", file=sys.stderr)
        return 1
    task_id = int(args[0])
    task = _find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1
    save_undo_snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")
    return 0


def _find_task(data, task_id):
    """Find a task by id. Returns the task dict or None."""
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def cmd_edit(args, data):
    """Handle 'edit' command."""
    new_title, task_id = _parse_edit_args(args)
    if task_id is None:
        print("Error: edit requires an ID", file=sys.stderr)
        return 1
    if new_title is None:
        print("Error: edit requires --title NEW_TITLE", file=sys.stderr)
        return 1
    task = _find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1
    save_undo_snapshot(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")
    return 0


def _parse_edit_args(args):
    """Parse edit arguments. Returns (new_title, task_id)."""
    positional = []
    new_title = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--title":
            i += 1
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            continue
        else:
            positional.append(a)
        i += 1
    task_id = None
    if positional:
        try:
            task_id = int(positional[0])
        except ValueError:
            pass
    return new_title, task_id


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        print("Error: search requires TEXT", file=sys.stderr)
        return 1
    text = " ".join(args).lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return 0
    for t in matches:
        print(task_line(t))
    return 0


def cmd_export(args, data):
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
        print("Error: export requires --format json|csv", file=sys.stderr)
        return 1

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
                "due": t.get("due", None),
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    return 0


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")
    return 0


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        return 1
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    cmd = sys.argv[1]
    rest = sys.argv[2:]

    handlers = {
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

    handler = handlers.get(cmd)
    if handler is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

    rc = handler(rest, data)
    sys.exit(rc if rc else 0)


if __name__ == "__main__":
    main()
