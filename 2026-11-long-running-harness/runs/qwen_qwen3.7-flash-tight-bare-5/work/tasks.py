#!/usr/bin/env python3
"""A command-line task manager."""

import json
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def snapshot(data):
    return {
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    }


def task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_add_args(args):
    title_parts = []
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
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    return " ".join(title_parts), priority, tags, due


def parse_edit_args(args):
    new_title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing value for --title", file=sys.stderr)
                sys.exit(1)
            parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title_parts.extend(parts)
        else:
            i += 1
    if not new_title_parts:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    return " ".join(new_title_parts)


def find_task(data, task_id):
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def do_add(args):
    title, priority, tags, due = parse_add_args(args)
    data = load_data()
    data["undo_history"].append(snapshot(data))
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


def do_list(args):
    data = load_data()
    sort_priority = False
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            if args[i + 1] == "priority":
                sort_priority = True
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

    tasks = data["tasks"]
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t["tags"]]
    if overdue:
        if today is None:
            today = date.today().isoformat()
        try:
            today_dt = datetime.strptime(today, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date: {today}", file=sys.stderr)
            sys.exit(1)
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def do_done(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task ID: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = find_task(data, task_id)
    data["undo_history"].append(snapshot(data))
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def do_delete(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task ID: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = find_task(data, task_id)
    data["undo_history"].append(snapshot(data))
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task ID: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = find_task(data, task_id)
    new_title = parse_edit_args(args[1:])
    data["undo_history"].append(snapshot(data))
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def do_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    data = load_data()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(task_line(task))


def do_export(args):
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
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            done_str = "true" if t["done"] else "false"
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def do_stats(args):
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(args):
    data = load_data()
    if not data["undo_history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["undo_history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    commands = {
        "add": do_add,
        "list": do_list,
        "done": do_done,
        "delete": do_delete,
        "edit": do_edit,
        "search": do_search,
        "export": do_export,
        "stats": do_stats,
        "undo": do_undo,
    }
    handler = commands.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    handler(args)


if __name__ == "__main__":
    main()
