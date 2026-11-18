#!/usr/bin/env python3
"""Command-line task manager using only Python 3 standard library."""

import json
import os
import sys
import copy
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_undo(data, state_before):
    """Record the current state for potential undo."""
    data["history"].append(copy.deepcopy(state_before))


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string. Returns the date object or None."""
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
        if parsed.strftime("%Y-%m-%d") != date_str:
            return None
        return parsed
    except (ValueError, TypeError):
        return None


def format_task_line(task):
    """Format a task as a display line with suffixes."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"

    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"

    tags = task.get("tags", [])
    for tag in tags:
        line += f" #{tag}"

    due = task.get("due", None)
    if due:
        line += f" due:{due}"

    return line


def find_task(data, task_id):
    """Find a task by id. Returns the task dict or None."""
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def main():
    args = sys.argv[1:]
    if not args:
        print("Error: No command provided", file=sys.stderr)
        sys.exit(1)

    command = args[0]
    raw_args = args[1:]

    # Parse options
    opts = {
        "_priority": None,
        "_tags": [],
        "_due": None,
        "_sort": None,
        "_tag_filter": None,
        "_overdue": False,
        "_today": None,
        "_format": None,
        "_edit_title": None,
        "_positional": [],
    }

    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg == "--priority":
            i += 1
            if i >= len(raw_args):
                print("Error: --priority requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_priority"] = raw_args[i]
        elif arg == "--tag":
            i += 1
            if i >= len(raw_args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_tags"].append(raw_args[i])
        elif arg == "--due":
            i += 1
            if i >= len(raw_args):
                print("Error: --due requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_due"] = raw_args[i]
        elif arg == "--sort":
            i += 1
            if i >= len(raw_args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_sort"] = raw_args[i]
        elif arg == "--overdue":
            opts["_overdue"] = True
        elif arg == "--today":
            i += 1
            if i >= len(raw_args):
                print("Error: --today requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_today"] = raw_args[i]
        elif arg == "--format":
            i += 1
            if i >= len(raw_args):
                print("Error: --format requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_format"] = raw_args[i]
        elif arg == "--title":
            i += 1
            if i >= len(raw_args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts = [raw_args[i]]
            j = i + 1
            while j < len(raw_args) and not raw_args[j].startswith("--"):
                title_parts.append(raw_args[j])
                j += 1
            opts["_edit_title"] = " ".join(title_parts)
            i = j - 1
        elif arg.startswith("--tag="):
            opts["_tag_filter"] = arg[6:]
        else:
            opts["_positional"].append(arg)
        i += 1

    # Load data
    data = load_data()

    # Record state before mutation commands
    def record_undo_point():
        record_undo(data, copy.deepcopy(data))

    # Dispatch commands
    if command == "add":
        if not opts["_positional"]:
            print("Error: add requires a title", file=sys.stderr)
            sys.exit(1)
        title = " ".join(opts["_positional"])
        priority = opts["_priority"]
        if priority is not None:
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
        else:
            priority = "medium"
        due = opts["_due"]
        if due is not None:
            validated = validate_date(due)
            if validated is None:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
        record_undo_point()
        task = {
            "id": data["next_id"],
            "title": title,
            "done": False,
            "priority": priority,
            "tags": list(opts["_tags"]),
            "due": due,
        }
        data["tasks"].append(task)
        data["next_id"] += 1
        save_data(data)
        print(f"Added {task['id']}")

    elif command == "list":
        tasks = list(data["tasks"])
        if opts["_tag_filter"]:
            tag = opts["_tag_filter"]
            tasks = [t for t in tasks if tag in t.get("tags", [])]
        if opts["_overdue"]:
            today_str = opts["_today"]
            if today_str:
                today = validate_date(today_str)
            else:
                today = date.today()
            if today is None:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
            tasks = [
                t for t in tasks
                if not t["done"] and t.get("due")
                and validate_date(t["due"]) < today
            ]
        if opts["_sort"] == "priority":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
        else:
            tasks = sorted(tasks, key=lambda t: t["id"])
        if not tasks:
            print("No tasks")
        else:
            for task in tasks:
                print(format_task_line(task))

    elif command == "done":
        if not opts["_positional"]:
            print("Error: done requires an ID", file=sys.stderr)
            sys.exit(1)
        try:
            task_id = int(opts["_positional"][0])
        except ValueError:
            print(f"No such task: {opts['_positional'][0]}", file=sys.stderr)
            sys.exit(1)
        task = find_task(data, task_id)
        if task is None:
            print(f"No such task: {task_id}", file=sys.stderr)
            sys.exit(1)
        record_undo_point()
        task["done"] = True
        save_data(data)
        print(f"Done {task_id}")

    elif command == "delete":
        if not opts["_positional"]:
            print("Error: delete requires an ID", file=sys.stderr)
            sys.exit(1)
        try:
            task_id = int(opts["_positional"][0])
        except ValueError:
            print(f"No such task: {opts['_positional'][0]}", file=sys.stderr)
            sys.exit(1)
        task = find_task(data, task_id)
        if task is None:
            print(f"No such task: {task_id}", file=sys.stderr)
            sys.exit(1)
        record_undo_point()
        data["tasks"].remove(task)
        save_data(data)
        print(f"Deleted {task_id}")

    elif command == "edit":
        if not opts["_positional"]:
            print("Error: edit requires an ID", file=sys.stderr)
            sys.exit(1)
        try:
            task_id = int(opts["_positional"][0])
        except ValueError:
            print(f"No such task: {opts['_positional'][0]}", file=sys.stderr)
            sys.exit(1)
        task = find_task(data, task_id)
        if task is None:
            print(f"No such task: {task_id}", file=sys.stderr)
            sys.exit(1)
        record_undo_point()
        if opts["_edit_title"] is not None:
            task["title"] = opts["_edit_title"]
        save_data(data)
        print(f"Edited {task_id}")

    elif command == "search":
        if not opts["_positional"]:
            print("Error: search requires text", file=sys.stderr)
            sys.exit(1)
        search_text = " ".join(opts["_positional"]).lower()
        matches = []
        for task in sorted(data["tasks"], key=lambda t: t["id"]):
            if search_text in task["title"].lower():
                matches.append(task)
        if not matches:
            print("No matches")
        else:
            for task in matches:
                print(format_task_line(task))

    elif command == "export":
        fmt = opts["_format"]
        if fmt not in ("json", "csv"):
            print(f"Error: unknown format '{fmt}'", file=sys.stderr)
            sys.exit(1)
        tasks = sorted(data["tasks"], key=lambda t: t["id"])
        if fmt == "json":
            result = []
            for task in tasks:
                result.append({
                    "id": task["id"],
                    "title": task["title"],
                    "done": task["done"],
                    "priority": task.get("priority", "medium"),
                    "tags": task.get("tags", []),
                    "due": task.get("due", None),
                })
            print(json.dumps(result))
        elif fmt == "csv":
            print("id,title,done,priority,tags,due")
            for task in tasks:
                tags_str = ";".join(task.get("tags", []))
                due_str = task.get("due", "")
                done_str = "true" if task["done"] else "false"
                print(f"{task['id']},{task['title']},{done_str},{task.get('priority', 'medium')},{tags_str},{due_str}")

    elif command == "stats":
        open_count = sum(1 for t in data["tasks"] if not t["done"])
        done_count = sum(1 for t in data["tasks"] if t["done"])
        total = len(data["tasks"])
        print(f"open: {open_count}")
        print(f"done: {done_count}")
        print(f"total: {total}")

    elif command == "undo":
        if not data["history"]:
            print("Nothing to undo", file=sys.stderr)
            sys.exit(1)
        previous_state = data["history"].pop()
        data["tasks"] = previous_state["tasks"]
        data["next_id"] = previous_state["next_id"]
        save_data(data)
        print("Undone")

    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
