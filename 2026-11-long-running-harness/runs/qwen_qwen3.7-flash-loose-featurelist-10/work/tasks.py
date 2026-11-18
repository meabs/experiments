#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task_line(task):
    check = "x" if task["done"] else " "
    line = f'{task["id"]} [{check}] {task["title"]}'
    if task.get("priority"):
        p = task["priority"]
        if p == "high":
            line += " (high)"
        elif p == "low":
            line += " (low)"
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing due date", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        elif arg.startswith("--"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)
        else:
            if title is None:
                title = arg
            i += 1
    if title is None:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task_id = data["next_id"]
    data["next_id"] += 1
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    sort_option = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_option = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("Missing date value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    if today_str is None:
        today = date.today().isoformat()
    else:
        today = today_str
    data = load_data()
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    if sort_option == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
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
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    task_id = None
    new_title = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
        else:
            if task_id is None:
                try:
                    task_id = int(arg)
                except ValueError:
                    print(f"No such task: {arg}", file=sys.stderr)
                    sys.exit(1)
            i += 1
    if task_id is None or new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    data = load_data()
    matches = []
    for t in data["tasks"]:
        if query in t["title"].lower():
            matches.append(t)
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
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
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority", "medium")},{tags_str},{due_str}')
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    history_file = DATA_FILE.replace(".json", "_history.json")
    if not os.path.exists(history_file):
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    with open(history_file, "r") as f:
        history = json.load(f)
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = history.pop()
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    data["tasks"] = previous_state["tasks"]
    data["next_id"] = previous_state["next_id"]
    save_data(data)
    print("Undone")


def save_undo_state():
    """Save current state for undo."""
    data = load_data()
    history_file = DATA_FILE.replace(".json", "_history.json")
    if not os.path.exists(history_file):
        history = []
    else:
        with open(history_file, "r") as f:
            history = json.load(f)
    history.append({
        "tasks": list(data["tasks"]),
        "next_id": data["next_id"],
    })
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


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

MUTATING_COMMANDS = {"add", "done", "delete", "edit"}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    # Save state before mutating commands
    if command in MUTATING_COMMANDS:
        save_undo_state()

    try:
        COMMANDS[command](args)
    except SystemExit as e:
        # If a mutating command failed, remove the last undo entry
        if command in MUTATING_COMMANDS and e.code == 1:
            history_file = DATA_FILE.replace(".json", "_history.json")
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    history = json.load(f)
                if history:
                    history.pop()
                    with open(history_file, "w") as f:
                        json.dump(history, f, indent=2)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
