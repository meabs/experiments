#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = ".tasks_history.json"


def load_tasks():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data["tasks"], data.get("next_id", 1)
    except FileNotFoundError:
        return {}, 1
    except (json.JSONDecodeError, KeyError):
        print("Error: corrupted data file", file=sys.stderr)
        sys.exit(1)


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        return data.get("history", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump({"history": history}, f)


def format_task(task):
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


def parse_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


def get_priority_sort_key(priority):
    order = {"high": 0, "medium": 1, "low": 2}
    return order.get(priority, 1)


def parse_args(args):
    positional = []
    options = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if key in ("tag", "priority", "due", "sort", "format", "today", "title"):
                if i + 1 < len(args):
                    val = args[i + 1]
                    if key == "tag":
                        options.setdefault(key, []).append(val)
                    elif key in ("priority", "due", "sort", "format", "today", "title"):
                        options[key] = val
                    i += 2
                else:
                    options[key] = ""
                    i += 1
            elif key in ("overdue",):
                options[key] = True
                i += 1
            else:
                i += 1
        else:
            positional.append(arg)
            i += 1
    return positional, options


def cmd_add(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    if not positional:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(positional)
    priority = options.get("priority", "medium")
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)
    due = options.get("due", None)
    if due is not None:
        parsed = parse_date(due)
        if parsed is None:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)
    tags = options.get("tag", [])
    task_id = next_id
    tasks[str(task_id)] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    next_id += 1
    save_tasks(tasks, next_id)
    print(f"Added {task_id}")


def cmd_list(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    task_list = sorted(tasks.values(), key=lambda t: t["id"])
    if "tag" in options:
        tag_filter = options["tag"]
        task_list = [t for t in task_list if tag_filter in t["tags"]]
    if options.get("overdue", False):
        today_str = options.get("today", str(date.today()))
        today_parsed = parse_date(today_str)
        if today_parsed is None:
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        task_list = [
            t for t in task_list
            if t["due"] is not None
            and t["due"] < today_parsed
            and not t["done"]
        ]
    if not task_list:
        print("No tasks")
        return
    if options.get("sort") == "priority":
        task_list.sort(key=lambda t: (get_priority_sort_key(t["priority"]), t["id"]))
    for task in task_list:
        print(format_task(task))


def cmd_done(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    if not positional:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print(f"No such task: {positional[0]}", file=sys.stderr)
        sys.exit(1)
    key = str(task_id)
    if key not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    tasks[key]["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    if not positional:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print(f"No such task: {positional[0]}", file=sys.stderr)
        sys.exit(1)
    key = str(task_id)
    if key not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    del tasks[key]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    if not positional:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print(f"No such task: {positional[0]}", file=sys.stderr)
        sys.exit(1)
    key = str(task_id)
    if key not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    if "title" not in options:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    tasks[key]["title"] = options["title"]
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    if not positional:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(positional).lower()
    matches = sorted(
        [t for t in tasks.values() if search_text in t["title"].lower()],
        key=lambda t: t["id"]
    )
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(tasks, next_id):
    positional, options = parse_args(sys.argv[2:])
    fmt = options.get("format", "json")
    task_list = sorted(tasks.values(), key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in task_list:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in task_list:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t["due"] if t["due"] else "",
            ])
        print(output.getvalue().rstrip("\n"))
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(tasks, next_id):
    task_list = tasks.values()
    total = len(task_list)
    done_count = sum(1 for t in task_list if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(tasks, next_id):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_state = history.pop()
    save_history(history)
    # Restore previous state
    saved_tasks = prev_state["tasks"]
    saved_next_id = prev_state["next_id"]
    save_tasks(saved_tasks, saved_next_id)
    print("Undone")


MUTATING_COMMANDS = ("add", "done", "delete", "edit")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    tasks, next_id = load_tasks()
    
    if command == "undo":
        cmd_undo(tasks, next_id)
        return
    
    if command in MUTATING_COMMANDS:
        # Save state before mutation for undo
        history = load_history()
        history.append({
            "tasks": copy.deepcopy(tasks),
            "next_id": next_id,
        })
        save_history(history)
    
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
    
    handler = commands.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    
    handler(tasks, next_id)


if __name__ == "__main__":
    main()
