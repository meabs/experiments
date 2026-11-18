#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {status} {task['title']}"]

    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")

    tags = task.get("tags", [])
    if tags:
        parts.extend(tags)

    if task.get("due"):
        parts.append(f"due:{task['due']}")

    return " ".join(parts)


def push_state(tasks, next_id):
    history = load_undo()
    history.append({"tasks": tasks, "next_id": next_id})
    save_undo(history)


def cmd_add(args):
    tasks = load_tasks()
    title_parts = []
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
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    next_id = get_next_id(tasks)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    push_state(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks = load_tasks()
    sort_mode = None
    tag_filter = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            today_str = None
            if i + 1 >= len(args):
                today_str = date.today().isoformat()
                i += 1
            else:
                i += 1
                if i < len(args) and args[i] == "--today":
                    if i + 1 >= len(args):
                        print("Missing today date", file=sys.stderr)
                        sys.exit(1)
                    today_str = args[i + 1]
                    i += 2
                else:
                    today_str = args[i]
                    i += 1
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
            filtered = []
            for t in tasks:
                if t["done"]:
                    continue
                if not t.get("due"):
                    continue
                if t["due"] < today_str:
                    filtered.append(t)
            tasks = filtered
        else:
            i += 1

    if sort_mode == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break

    if found is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    found["done"] = True
    push_state(tasks, get_next_id(tasks) + 1)
    print(f"Done {tid}")


def cmd_delete(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break

    if found is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    tasks = [t for t in tasks if t["id"] != tid]
    push_state(tasks, get_next_id(tasks) + 1)
    print(f"Deleted {tid}")


def cmd_edit(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break

    if found is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    i = 1
    new_title = None
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    found["title"] = new_title
    push_state(tasks, get_next_id(tasks) + 1)
    print(f"Edited {tid}")


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)

    text = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        print("Unknown format", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    tasks = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        out = []
        for t in tasks:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(out, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_undo()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    state = history.pop()
    save_undo(history)
    save_tasks(state["tasks"])
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
