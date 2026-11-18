#!/usr/bin/env python3
"""A command-line task manager."""

import json
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    try:
        with open(UNDO_FILE, "r") as f:
            result = json.load(f)
            return result if isinstance(result, dict) else {"history": []}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"history": []}


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]

    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")

    for tag in task["tags"]:
        parts.append(f"#{tag}")

    if task["due"]:
        parts.append(f"due:{task['due']}")

    return " ".join(parts)


def validate_date(date_str):
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return False
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        date(year, month, day)
        return True
    except (ValueError, TypeError):
        return False


def cmd_add(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due = args[i]
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
        else:
            title_parts.append(arg)
        i += 1

    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tasks, next_id = load_tasks()

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    next_id += 1
    save_tasks(tasks, next_id)
    record_mutation(tasks, next_id)
    print(f"Added {task['id']}")


def cmd_list(args):
    tasks, _ = load_tasks()

    sort_mode = None
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i]
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                print("Missing value for --today", file=sys.stderr)
                sys.exit(1)
            today_str = args[i]
        i += 1

    today = date.today().isoformat() if today_str is None else today_str

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    if overdue:
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break

    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    save_tasks(tasks, next_id)
    record_mutation(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]

    if len(new_tasks) == len(tasks):
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    save_tasks(new_tasks, next_id)
    record_mutation(new_tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task ID: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    new_title = None

    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break

    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    save_tasks(tasks, next_id)
    record_mutation(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)

    query = " ".join(args).lower()
    tasks, _ = load_tasks()

    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                print("Missing value for --format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i]
        i += 1

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for task in tasks:
            result.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task["tags"],
                "due": task["due"],
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task["tags"])
            due_str = task["due"] if task["due"] else ""
            print(f"{task['id']},{task['title']},{done_str},{task['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_undo_history()
    if not history["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = history["history"].pop()
    save_undo_history(history)

    save_tasks(prev_state["tasks"], prev_state["next_id"])
    print("Undone")


def record_mutation(tasks, next_id):
    history = load_undo_history()
    history["history"].append({"tasks": tasks, "next_id": next_id})
    save_undo_history(history)


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

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
