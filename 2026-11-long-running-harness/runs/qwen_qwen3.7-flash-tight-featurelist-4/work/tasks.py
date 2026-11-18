#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    suffixes = []
    p = task.get("priority", "medium")
    if p == "high":
        suffixes.append("(high)")
    elif p == "low":
        suffixes.append("(low)")
    tags = task.get("tags", [])
    if tags:
        suffixes.extend(tags)
    due = task.get("due")
    if due:
        suffixes.append(f"due:{due}")
    parts = [f'{task["id"]} {status} {task["title"]}'] + suffixes
    return " ".join(parts)


def cmd_add(args):
    data = load_data()
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("--priority requires a value")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due = args[i + 1]
            try:
                import calendar
                parts = due.split("-")
                if len(parts) != 3:
                    raise ValueError
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                max_day = calendar.monthrange(year, month)[1]
                if day > max_day:
                    raise ValueError
            except (ValueError, IndexError):
                error(f"Invalid date: {due}")
            i += 2
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            if title is None:
                title = arg
            else:
                title += " " + arg
            i += 1

    if title is None:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")

    prev_state = {
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["undo_stack"].append(prev_state)
    save_data(data)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"])
    sort_mode = None
    tag_filter = None
    overdue = False
    today = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_mode = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                error("--today requires a value")
            today = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        if today is None:
            import datetime
            today = datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    elif sort_mode:
        error(f"Unknown sort mode: {sort_mode}")

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    data = load_data()
    if not args:
        error("Usage: done ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    prev_state = {
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["undo_stack"].append(prev_state)
    save_data(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    data = load_data()
    if not args:
        error("Usage: delete ID")
    task_id = int(args[0])
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")
    prev_state = {
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["undo_stack"].append(prev_state)
    save_data(data)
    data["tasks"].remove(task)
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    data = load_data()
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    task_id = int(args[0])
    new_title = None
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            new_title = args[i + 1]
            i += 1
            while i < len(args):
                if args[i].startswith("--"):
                    break
                new_title += " " + args[i]
                i += 1
        else:
            error(f"Unknown option: {arg}")
        i += 1

    if new_title is None:
        error("--title is required")

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        error(f"No such task: {task_id}")

    prev_state = {
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["undo_stack"].append(prev_state)
    save_data(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    data = load_data()
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args).lower()
    matches = []
    for task in data["tasks"]:
        if text in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    data = load_data()
    format_type = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                error("--format requires a value")
            format_type = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {arg}")

    if format_type is None:
        error("Usage: export --format json|csv")

    if format_type == "json":
        result = []
        for task in data["tasks"]:
            result.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(result))
    elif format_type == "csv":
        print("id,title,done,priority,tags,due")
        for task in data["tasks"]:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f'{task["id"]},{task["title"]},{"true" if task["done"] else "false"},{task.get("priority", "medium")},{tags_str},{due_str}')
    else:
        error(f"Unknown format: {format_type}")


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["undo_stack"]:
        error("Nothing to undo")
    prev_state = data["undo_stack"].pop()
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
        error("Usage: python3 tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
