#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "undo_history": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"tasks": {}, "next_id": 1, "undo_history": []}


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"
    
    # Priority suffix (feature 5)
    if task.get("priority"):
        p = task["priority"]
        if p != "medium":
            line += f" ({p})"
    
    # Tags suffix (feature 6)
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    
    # Due date suffix (feature 7)
    if task.get("due"):
        line += f" due:{task['due']}"
    
    return line


def cmd_add(args, data):
    """Add a new task."""
    priority = "medium"
    tags = []
    due = None
    
    i = 0
    title_parts = []
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
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    
    title = " ".join(title_parts)
    
    tid = data["next_id"]
    data["tasks"][tid] = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = tid + 1
    
    data["undo_history"].append(json.dumps({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }))
    
    save_data(data)
    print(f"Added {tid}")


def cmd_list(args, data):
    """List tasks."""
    sort_option = None
    filter_tag = None
    overdue = False
    today = None
    
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            sort_option = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
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
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)
    
    if today is None:
        today = date.today().isoformat()
    
    tasks = list(data["tasks"].values())
    
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    
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
    
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    
    data["tasks"][tid]["done"] = True
    
    data["undo_history"].append(json.dumps({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }))
    
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Delete a task."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    
    del data["tasks"][tid]
    
    data["undo_history"].append(json.dumps({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }))
    
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Edit a task."""
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    
    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing value for --title", file=sys.stderr)
                sys.exit(1)
            title_parts.append(args[i + 1])
            i += 2
        else:
            i += 1
    
    if not title_parts:
        print("Missing new title", file=sys.stderr)
        sys.exit(1)
    
    data["tasks"][tid]["title"] = " ".join(title_parts)
    
    data["undo_history"].append(json.dumps({
        "tasks": dict(data["tasks"]),
        "next_id": data["next_id"],
    }))
    
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Search tasks by title."""
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    
    query = " ".join(args).lower()
    tasks = [t for t in data["tasks"].values() if query in t["title"].lower()]
    tasks.sort(key=lambda t: t["id"])
    
    if not tasks:
        print("No matches")
        return
    
    for task in tasks:
        print(task_line(task))


def cmd_export(args, data):
    """Export tasks."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    
    if not fmt or fmt not in ("json", "csv"):
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
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    """Show task statistics."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    """Undo the last mutating command."""
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    
    prev_state = json.loads(data["undo_history"].pop())
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
    
    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
