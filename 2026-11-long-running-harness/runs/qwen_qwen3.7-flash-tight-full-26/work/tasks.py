#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = ".undo_state.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return {"history": [], "next_id": 1}
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(state):
    with open(UNDO_FILE, "w") as f:
        json.dump(state, f)


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def validate_date(d):
    try:
        date.fromisoformat(d)
    except (ValueError, TypeError):
        print(f"Invalid date: {d}", file=sys.stderr)
        sys.exit(1)


def record_undo(undo_state, prev_tasks, next_id_before):
    undo_state["history"].append({
        "tasks": prev_tasks,
        "next_id": next_id_before,
    })
    save_undo(undo_state)


def format_task_line(task):
    done_mark = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {done_mark} {task["title"]}'
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    undo_state = load_undo()
    tasks = load_tasks()
    next_id = undo_state.get("next_id", get_next_id(tasks))

    priority = None
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            i += 1
            if i >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i])
        elif args[i] == "--due":
            i += 1
            if i >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i]
            validate_date(due)
        else:
            title_parts.append(args[i])
        i += 1

    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    record_undo(undo_state, tasks, next_id)

    tasks.append(task)
    undo_state["next_id"] = next_id + 1
    save_undo(undo_state)
    save_tasks(tasks)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks = load_tasks()

    sort_mode = None
    filter_tag = None
    overdue = False
    today_arg = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            i += 1
            if i >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i]
        elif args[i] == "--tag":
            i += 1
            if i >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i]
        elif args[i] == "--overdue":
            overdue = True
        elif args[i] == "--today":
            i += 1
            if i >= len(args):
                print("--today requires a date", file=sys.stderr)
                sys.exit(1)
            today_arg = args[i]
        i += 1

    if today_arg:
        validate_date(today_arg)
        today = date.fromisoformat(today_arg)
    else:
        today = date.today()

    filtered = tasks[:]

    if filter_tag:
        filtered = [t for t in filtered if filter_tag in t.get("tags", [])]

    if overdue:
        filtered = [t for t in filtered if not t["done"]]
        if today_arg:
            filtered = [t for t in filtered if t.get("due") and t["due"] < today_arg]
        else:
            filtered = [t for t in filtered if t.get("due") and t["due"] < today.isoformat()]

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2, None: 3}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority"), 3), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)

    undo_state = load_undo()
    tasks = load_tasks()

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    record_undo(undo_state, tasks, undo_state.get("next_id", get_next_id(tasks)))

    task["done"] = True
    save_tasks(tasks)
    save_undo(undo_state)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)

    undo_state = load_undo()
    tasks = load_tasks()

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    record_undo(undo_state, tasks, undo_state.get("next_id", get_next_id(tasks)))

    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    save_undo(undo_state)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    undo_state = load_undo()
    tasks = load_tasks()

    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            title_parts = []
            while i < len(args) and args[i] != "--title":
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        i += 1

    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    record_undo(undo_state, tasks, undo_state.get("next_id", get_next_id(tasks)))

    task["title"] = new_title
    save_tasks(tasks)
    save_undo(undo_state)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    query = " ".join(args).lower()

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
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i]
        i += 1

    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","")},{tags_str},{due_str}')
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "undo":
        cmd_undo()
    elif command in COMMANDS:
        COMMANDS[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
