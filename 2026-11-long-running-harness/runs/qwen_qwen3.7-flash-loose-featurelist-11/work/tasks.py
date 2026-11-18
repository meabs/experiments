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
        raw = json.load(f)
    tasks = {}
    for tid_str, task in raw.get("tasks", {}).items():
        tid = int(tid_str)
        task["id"] = tid
        tasks[tid] = task
    return {
        "tasks": tasks,
        "next_id": raw.get("next_id", 1),
        "undo_stack": raw.get("undo_stack", []),
    }


def save_data(data):
    """Persist tasks and state to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_tasks(data):
    """Get all tasks sorted by id."""
    return sorted(data["tasks"].values(), key=lambda t: t["id"])


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args, data):
    if not args:
        print("Missing title", file=sys.stderr)
        return 1
    priority = "medium"
    tags = []
    due = None
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                return 1
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                return 1
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                return 1
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                return 1
            due = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1
    title = " ".join(positional)
    undo_entry = {
        "type": "add",
        "state": {
            "tasks": dict(data["tasks"]),
            "next_id": data["next_id"],
        }
    }
    data["undo_stack"].append(undo_entry)
    tid = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][tid] = task
    save_data(data)
    print(f"Added {tid}")
    return 0


def cmd_list(args, data):
    sort_mode = None
    filter_tag = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                return 1
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                return 1
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing value for --today", file=sys.stderr)
                return 1
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1
    tasks = get_tasks(data)
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        import datetime
        today = datetime.date.fromisoformat(today_arg) if today_arg else datetime.date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today.isoformat()]
    if not tasks:
        print("No tasks")
        return 0
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    for t in tasks:
        print(task_line(t))
    return 0


def cmd_done(args, data):
    if not args:
        print("Missing task ID", file=sys.stderr)
        return 1
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        return 1
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        return 1
    undo_entry = {
        "type": "done",
        "state": {
            "tasks": dict(data["tasks"]),
            "next_id": data["next_id"],
        }
    }
    data["undo_stack"].append(undo_entry)
    data["tasks"][tid]["done"] = True
    save_data(data)
    print(f"Done {tid}")
    return 0


def cmd_delete(args, data):
    if not args:
        print("Missing task ID", file=sys.stderr)
        return 1
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        return 1
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        return 1
    undo_entry = {
        "type": "delete",
        "state": {
            "tasks": dict(data["tasks"]),
            "next_id": data["next_id"],
        }
    }
    data["undo_stack"].append(undo_entry)
    del data["tasks"][tid]
    save_data(data)
    print(f"Deleted {tid}")
    return 0


def cmd_edit(args, data):
    if not args:
        print("Missing task ID", file=sys.stderr)
        return 1
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        return 1
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        return 1
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing value for --title", file=sys.stderr)
                return 1
            new_title = " ".join(args[i + 1:])
            break
        i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        return 1
    undo_entry = {
        "type": "edit",
        "state": {
            "tasks": dict(data["tasks"]),
            "next_id": data["next_id"],
        }
    }
    data["undo_stack"].append(undo_entry)
    data["tasks"][tid]["title"] = new_title
    save_data(data)
    print(f"Edited {tid}")
    return 0


def cmd_search(args, data):
    if not args:
        print("Missing search text", file=sys.stderr)
        return 1
    query = " ".join(args).lower()
    matches = [t for t in get_tasks(data) if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return 0
    for t in matches:
        print(task_line(t))
    return 0


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing value for --format", file=sys.stderr)
                return 1
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        print(f"Unknown format: {fmt}", file=sys.stderr)
        return 1
    tasks = get_tasks(data)
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
    return 0


def cmd_stats(args, data):
    tasks = data["tasks"].values()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")
    return 0


def cmd_undo(args, data):
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        return 1
    entry = data["undo_stack"].pop()
    data["tasks"] = entry["state"]["tasks"]
    data["next_id"] = entry["state"]["next_id"]
    save_data(data)
    print("Undone")
    return 0


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
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    exit_code = COMMANDS[command](sys.argv[2:], data)
    save_data(data)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
