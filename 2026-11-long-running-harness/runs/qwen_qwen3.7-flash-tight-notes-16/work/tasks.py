#!/usr/bin/env python3
"""Command-line task manager."""

import sys
import json
import os
import copy
from datetime import datetime, date

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "next_id": 1}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def add_state_to_history(data):
    history = load_history()
    history.append(copy.deepcopy(data))
    if len(history) > 100:
        history.pop(0)
    save_history(history)


def parse_args(argv):
    """Parse arguments starting from index 0 as options/positional values.
    The command name should be passed separately."""
    result = {
        "command": None,
        "positional": [],
        "options": {},
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--priority":
            if i + 1 >= len(argv):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            result["options"]["priority"] = argv[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(argv):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            if "tags" not in result["options"]:
                result["options"]["tags"] = []
            result["options"]["tags"].append(argv[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(argv):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            result["options"]["due"] = argv[i + 1]
            i += 2
        elif arg == "--title":
            if i + 1 >= len(argv):
                print("Missing value for --title", file=sys.stderr)
                sys.exit(1)
            result["options"]["title"] = " ".join(argv[i + 1:])
            break
        elif arg == "--sort":
            if i + 1 >= len(argv):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            result["options"]["sort"] = argv[i + 1]
            i += 2
        elif arg == "--overdue":
            result["options"]["overdue"] = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(argv):
                print("Missing value for --today", file=sys.stderr)
                sys.exit(1)
            result["options"]["today"] = argv[i + 1]
            i += 2
        elif arg == "--format":
            if i + 1 >= len(argv):
                print("Missing value for --format", file=sys.stderr)
                sys.exit(1)
            result["options"]["format"] = argv[i + 1]
            i += 2
        elif arg.startswith("--"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)
        else:
            result["positional"].append(arg)
            i += 1
    return result


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        for tag in task["tags"]:
            line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    title = args["positional"][0] if args["positional"] else ""
    if not title:
        print("Error: No title provided", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    priority = args["options"].get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    due = args["options"].get("due", None)
    if due is not None:
        if not validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    tags = args["options"].get("tags", [])

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
    save_data(data)
    add_state_to_history(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    data = load_data()
    tasks = list(data["tasks"])

    if "tag" in args["options"]:
        filter_tag = args["options"]["tag"]
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if args["options"].get("overdue"):
        today_str = args["options"].get("today", date.today().isoformat())
        if not validate_date(today_str):
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    if not tasks:
        print("No tasks")
        return

    sort_opt = args["options"].get("sort")
    if sort_opt == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    task_id = int(args["positional"][0])
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["done"] = True
    save_data(data)
    add_state_to_history(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    task_id = int(args["positional"][0])
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    add_state_to_history(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    task_id = int(args["positional"][0])
    data = load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = args["options"].get("title")
    if new_title is not None:
        task["title"] = new_title
    save_data(data)
    add_state_to_history(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    data = load_data()
    query = args["positional"][0].lower() if args["positional"] else ""
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    fmt = args["options"].get("format")
    if fmt not in ("json", "csv"):
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
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
                "due": t.get("due", None),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = history.pop()
    save_data(previous_state)
    save_history(history)
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
    args = parse_args(sys.argv[2:])
    args["command"] = command
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
