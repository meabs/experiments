#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"
HISTORY_FILE = "undo_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
        f.write("\n")


def push_history(tasks_data):
    history = load_history()
    history.append(json.dumps(tasks_data))
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = json.loads(history.pop())
    save_history(history)
    return prev_state


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        tag_suffix = " ".join(f"#{t}" for t in tags)
        line += f" {tag_suffix}"
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args):
    data = load_tasks()
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                parts = due.split("-")
                if len(parts) != 3:
                    raise ValueError
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if month < 1 or month > 12:
                    raise ValueError
                if day < 1 or day > 31:
                    raise ValueError
                days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                    days_in_month[2] = 29
                if day > days_in_month[month]:
                    raise ValueError
            except (ValueError, IndexError):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += f" {args[i]}"
            i += 1

    if title is None:
        print("Missing title", file=sys.stderr)
        sys.exit(1)

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
    push_history(data)
    save_tasks(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_tasks()
    tasks = data["tasks"]
    sort_priority = False
    filter_tag = None
    overdue = False
    today = None

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
            today = args[i + 1]
            i += 2
        else:
            i += 1

    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if overdue:
        if today is None:
            import datetime
            today = datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            push_history(data)
            save_tasks(data)
            print(f"Done {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"].pop(i)
            push_history(data)
            save_tasks(data)
            print(f"Deleted {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing new title", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
            while i < len(args) and not args[i].startswith("--"):
                new_title += f" {args[i]}"
                i += 1
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["title"] = new_title
            push_history(data)
            save_tasks(data)
            print(f"Edited {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    data = load_tasks()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    data = load_tasks()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')


def cmd_stats(args):
    data = load_tasks()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    prev_state = pop_history()
    save_tasks(prev_state)
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

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
