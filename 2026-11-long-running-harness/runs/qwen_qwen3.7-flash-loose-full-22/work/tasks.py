#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def format_task_line(task):
    """Format a task as a display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    """Handle 'add' command."""
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
                due = due_str
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)

    # Save state for undo
    data["undo_history"].append({
        "type": "add",
        "prev_tasks": dict(data["tasks"]),
        "prev_next_id": data["next_id"],
    })

    tid = data["next_id"]
    data["next_id"] += 1
    data["tasks"][str(tid)] = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_data(data)
    print(f"Added {tid}")


def cmd_list(args, data):
    """Handle 'list' command."""
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None
    today = date.today()

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
            i += 2
        else:
            i += 1

    tasks = list(data["tasks"].values())

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filter: only open tasks with due date before today
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due")
                 and date.fromisoformat(t["due"]) < today]

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(format_task_line(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    tid = int(args[0])
    tid_str = str(tid)
    if tid_str not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    data["undo_history"].append({
        "type": "done",
        "prev_tasks": dict(data["tasks"]),
        "prev_next_id": data["next_id"],
        "task_id": tid_str,
    })

    data["tasks"][tid_str]["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    tid = int(args[0])
    tid_str = str(tid)
    if tid_str not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    data["undo_history"].append({
        "type": "delete",
        "prev_tasks": dict(data["tasks"]),
        "prev_next_id": data["next_id"],
        "task_id": tid_str,
    })

    del data["tasks"][tid_str]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    tid = int(args[0])
    tid_str = str(tid)
    if tid_str not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1

    if new_title is None:
        print("Error: edit requires --title", file=sys.stderr)
        sys.exit(1)

    data["undo_history"].append({
        "type": "edit",
        "prev_tasks": dict(data["tasks"]),
        "prev_next_id": data["next_id"],
        "task_id": tid_str,
    })

    data["tasks"][tid_str]["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    matches = []
    for t in sorted(data["tasks"].values(), key=lambda x: x["id"]):
        if query in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task_line(t))


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

    if fmt is None or fmt not in ("json", "csv"):
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority','medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    entry = data["undo_history"].pop()
    data["tasks"] = entry["prev_tasks"]
    data["next_id"] = entry["prev_next_id"]
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
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
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
