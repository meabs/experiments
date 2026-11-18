#!/usr/bin/env python3
"""A command-line task manager."""

import copy
import csv
import io
import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"tasks": [], "next_id": 1, "history": []}
    except json.JSONDecodeError:
        print("Error: corrupted data file", file=sys.stderr)
        sys.exit(1)
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def push_history(data):
    snapshot = {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["history"].append(snapshot)


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def find_task(data, task_id):
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def cmd_add(args):
    if not args:
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Error: --priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Error: --due requires a value", file=sys.stderr)
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
        print("Error: missing title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    data = load_data()
    push_history(data)

    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] = task_id + 1

    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    data = load_data()
    if not data["tasks"]:
        print("No tasks")
        return

    tasks = list(data["tasks"])

    sort_by = None
    tag_filter = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            if sort_by not in ("priority",):
                print(f"Invalid sort option: {sort_by}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a value", file=sys.stderr)
                sys.exit(1)
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1

    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t["tags"]]

    if overdue:
        if today_arg is None:
            today_str = date.today().isoformat()
        else:
            today_str = today_arg
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today_str]

    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid id '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(data)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid id '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        print("Error: missing task id", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Error: invalid id '{args[0]}'", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            parts = []
            i += 1
            while i < len(args) and args[i] != "--title":
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
            continue
        i += 1

    if new_title is None:
        print("Error: --title is required", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(data)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Error: missing search text", file=sys.stderr)
        sys.exit(1)

    search_text = " ".join(args).lower()
    data = load_data()

    matches = []
    for task in sorted(data["tasks"], key=lambda t: t["id"]):
        if search_text in task["title"].lower():
            matches.append(task)

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
            if i + 1 >= len(args):
                print("Error: --format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print(f"Error: unknown format '{fmt}'", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Error: --format is required", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for task in tasks:
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task["tags"],
                "due": task["due"],
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in tasks:
            tags_str = ";".join(task["tags"])
            writer.writerow([
                task["id"],
                task["title"],
                str(task["done"]).lower(),
                task["priority"],
                tags_str,
                task["due"] if task["due"] else "",
            ])
        print(buf.getvalue(), end="")


def cmd_stats(args):
    data = load_data()
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    snapshot = data["history"].pop()
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]
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
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
