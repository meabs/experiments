#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        data.setdefault("tasks", [])
        data.setdefault("next_id", 1)
        data.setdefault("history", [])
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        sys.exit(1)


def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}", file=sys.stderr)
        sys.exit(1)


def push_history(data):
    snapshot = {"tasks": [dict(t) for t in data["tasks"]], "next_id": data["next_id"]}
    data["history"].append(snapshot)


def pop_history(data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    snapshot = data["history"].pop()
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def format_task_line(task):
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
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    if not args:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title_parts = []
    priority = None
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
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    push_history(data)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_date = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                print(f"Unknown sort option: {args[i + 1]}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            try:
                today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if today_date is None and overdue:
        today_date = date.today()

    data = load_data()
    tasks = list(data["tasks"])

    # Filter by tag
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Overdue filter
    if overdue and today_date is not None:
        filtered = []
        for t in tasks:
            if t.get("due") and not t["done"]:
                try:
                    due_d = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_d < today_date:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    # Sort by priority
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
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
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
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
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
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
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    text = " ".join(args).lower()

    data = load_data()
    matches = []
    for task in data["tasks"]:
        if text in task["title"].lower():
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
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    if fmt not in ("json", "csv"):
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

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
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{str(t['done']).lower()},{t.get('priority','medium')},{tags_str},{due_str}")


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
    pop_history(data)
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
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

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](args)


if __name__ == "__main__":
    main()
