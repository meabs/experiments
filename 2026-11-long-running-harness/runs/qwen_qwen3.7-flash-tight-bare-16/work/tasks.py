#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


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
        json.dump({"tasks": tasks}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    snapshot = {"tasks": tasks, "next_id": next_id}
    history = load_history()
    history.append(snapshot)
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        return None
    snapshot = history.pop()
    save_history(history)
    return snapshot["tasks"], snapshot["next_id"]


def parse_args(args):
    result = {
        "_args": [],
        "--priority": None,
        "--tag": [],
        "--due": None,
        "--sort": None,
        "--tag_filter": [],
        "--overdue": False,
        "--today": None,
        "--format": None,
        "--title": None,
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            result["--priority"] = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            result["--tag"].append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            result["--due"] = args[i + 1]
            i += 2
        elif arg == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            result["--sort"] = args[i + 1]
            i += 2
        elif arg == "--tag":
            # Already handled above, but this catches duplicates
            pass
        elif arg == "--tag_filter":
            if i + 1 >= len(args):
                print("--tag-filter requires a value", file=sys.stderr)
                sys.exit(1)
            result["--tag_filter"].append(args[i + 1])
            i += 2
        elif arg == "--overdue":
            result["--overdue"] = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
                sys.exit(1)
            result["--today"] = args[i + 1]
            i += 2
        elif arg == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            result["--format"] = args[i + 1]
            i += 2
        elif arg == "--title":
            i += 1
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            if not title_parts:
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            result["--title"] = " ".join(title_parts)
        else:
            result["_args"].append(arg)
            i += 1
    return result


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def find_task(tasks, task_id):
    for t in tasks:
        if t["id"] == task_id:
            return t
    return None


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def cmd_add(parsed):
    tasks = load_tasks()
    next_id = get_next_id(tasks)
    title = parsed["_args"][0] if parsed["_args"] else ""
    priority = parsed["--priority"]
    tags = parsed["--tag"]
    due = parsed["--due"]
    if priority is not None and priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)
    if due is not None:
        if not validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)
    if priority is None:
        priority = "medium"
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": list(tags),
        "due": due,
    }
    push_history(tasks, next_id)
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {next_id}")


def cmd_list(parsed):
    tasks = load_tasks()
    if not tasks:
        print("No tasks")
        return

    # Filter by tag
    tag_filter = parsed["--tag_filter"]
    if tag_filter:
        filtered = []
        for t in tasks:
            task_tags = set(t.get("tags", []))
            for tf in tag_filter:
                if tf in task_tags:
                    filtered.append(t)
                    break
        tasks = filtered

    # Filter overdue
    overdue = parsed["--overdue"]
    if overdue:
        today_str = parsed["--today"]
        if today_str:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    # Sort by priority
    sort_opt = parsed["--sort"]
    if sort_opt == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(parsed):
    tasks = load_tasks()
    task_id = int(parsed["_args"][0])
    task = find_task(tasks, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_history(tasks, get_next_id(tasks))
    task["done"] = True
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(parsed):
    tasks = load_tasks()
    task_id = int(parsed["_args"][0])
    task = find_task(tasks, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_history(tasks, get_next_id(tasks))
    tasks.remove(task)
    save_tasks(tasks)
    print(f"Deleted {task_id}")


def cmd_edit(parsed):
    tasks = load_tasks()
    task_id = int(parsed["_args"][0])
    task = find_task(tasks, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = parsed["--title"]
    if new_title is None:
        print("--title required", file=sys.stderr)
        sys.exit(1)
    push_history(tasks, get_next_id(tasks))
    task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(parsed):
    tasks = load_tasks()
    text = parsed["_args"][0] if parsed["_args"] else ""
    results = [t for t in tasks if text.lower() in t["title"].lower()]
    results.sort(key=lambda t: t["id"])
    if not results:
        print("No matches")
        return
    for t in results:
        print(task_line(t))


def cmd_export(parsed):
    tasks = load_tasks()
    fmt = parsed["--format"]
    if fmt is None:
        print("--format required", file=sys.stderr)
        sys.exit(1)
    if fmt == "json":
        export_data = []
        for t in sorted(tasks, key=lambda x: x["id"]):
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
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in sorted(tasks, key=lambda x: x["id"]):
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")


def cmd_stats(parsed):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(parsed):
    result = pop_history()
    if result is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = result
    save_tasks(tasks)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    parsed = parse_args(args)

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

    commands[command](parsed)


if __name__ == "__main__":
    main()
