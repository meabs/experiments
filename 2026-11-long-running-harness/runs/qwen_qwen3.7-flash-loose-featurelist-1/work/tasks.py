#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        next_id = data.get("next_id", 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def undo_cmd():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_history(history)
    save_tasks(previous["tasks"], previous["next_id"])
    print("Undone")


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task.get("priority"):
        p = task["priority"]
        if p == "high":
            line += " (high)"
        elif p == "low":
            line += " (low)"
    tags = task.get("tags", [])
    if tags:
        tag_str = " ".join(f"#{t}" for t in tags)
        line += f" {tag_str}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_args(args):
    parsed = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            parsed["priority"] = args[i + 1]
            i += 2
        elif arg == "--tag":
            if "tags" not in parsed:
                parsed["tags"] = []
            parsed["tags"].append(args[i + 1])
            i += 2
        elif arg == "--due":
            parsed["due"] = args[i + 1]
            i += 2
        elif arg == "--title":
            parsed["title"] = " ".join(args[i + 1:])
            i = len(args)
        elif arg == "--sort":
            parsed["sort"] = args[i + 1]
            i += 2
        elif arg == "--overdue":
            parsed["overdue"] = True
            i += 1
        elif arg == "--today":
            parsed["today"] = args[i + 1]
            i += 2
        elif arg == "--format":
            parsed["format"] = args[i + 1]
            i += 2
        else:
            i += 1
    return parsed


def cmd_add(args):
    if not args:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title_parts = []
    options = []
    found_option = False
    for arg in args:
        if arg.startswith("--"):
            found_option = True
            options.append(arg)
        elif found_option:
            options.append(arg)
        else:
            title_parts.append(arg)
    title = " ".join(title_parts)
    if not title:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    parsed = parse_args(options)
    priority = parsed.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)
    due = parsed.get("due")
    if due:
        try:
            parts = due.split("-")
            if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                raise ValueError
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            date(y, m, d)
        except (ValueError, IndexError):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)
    tasks, next_id = load_tasks()
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": parsed.get("tags", []),
        "due": due,
    }
    push_history(tasks, next_id)
    tasks.append(task)
    next_id += 1
    save_tasks(tasks, next_id)
    print(f"Added {task['id']}")


def cmd_list(args):
    parsed = parse_args(args)
    tasks, next_id = load_tasks()
    if not tasks:
        print("No tasks")
        return
    result = list(tasks)
    if "tag" in parsed:
        tag_filter = parsed["tag"]
        result = [t for t in result if tag_filter in t.get("tags", [])]
    if parsed.get("overdue"):
        today_str = parsed.get("today", date.today().isoformat())
        try:
            today_parts = today_str.split("-")
            date(int(today_parts[0]), int(today_parts[1]), int(today_parts[2]))
        except (ValueError, IndexError):
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        result = [t for t in result if not t["done"] and t.get("due") and t["due"] < today_str]
    if parsed.get("sort") == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    for task in result:
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    push_history(tasks, next_id)
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks, next_id)
            print(f"Done {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    push_history(tasks, next_id)
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            save_tasks(tasks, next_id)
            print(f"Deleted {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    parsed = parse_args(args[1:])
    if "title" not in parsed:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    push_history(tasks, next_id)
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = parsed["title"]
            save_tasks(tasks, next_id)
            print(f"Edited {task_id}")
            return
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    tasks, next_id = load_tasks()
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    parsed = parse_args(args)
    if "format" not in parsed:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    fmt = parsed["format"]
    tasks, next_id = load_tasks()
    if fmt == "json":
        output = []
        for task in sorted(tasks, key=lambda t: t["id"]):
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in sorted(tasks, key=lambda t: t["id"]):
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due", "")
            print(f"{task['id']},{task['title']},{str(task['done']).lower()},{task.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, next_id = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


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
        "undo": lambda a: undo_cmd(),
    }
    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
