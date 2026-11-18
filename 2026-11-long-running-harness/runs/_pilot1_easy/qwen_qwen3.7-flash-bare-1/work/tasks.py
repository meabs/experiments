#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import copy
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data["tasks"]
    except (FileNotFoundError, KeyError):
        return []


def save_data(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        return data.get("history", [])
    except (FileNotFoundError, KeyError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump({"history": history}, f, indent=2)


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    for tag in tags:
        line += " #{}".format(tag)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def push_state(tasks):
    history = load_history()
    history.append(copy.deepcopy(tasks))
    save_history(history)


def undo(args):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev_tasks = history.pop()
    save_history(history)
    save_data(prev_tasks)
    print("Undone")


def cmd_add(args):
    title_parts = []
    priority = None
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Invalid date: ", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(due), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)

    valid_priorities = ("high", "medium", "low")
    if priority is not None and priority not in valid_priorities:
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)

    if priority is None:
        priority = "medium"

    tasks = load_data()
    push_state(tasks)

    task_id = get_next_id(tasks)
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_data(tasks)
    print("Added {}".format(task_id))


def cmd_list(args):
    tasks = load_data()
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    if overdue or filter_tag or sort_priority:
        filtered = []
        for t in tasks:
            if filter_tag and filter_tag not in t.get("tags", []):
                continue
            if overdue:
                today = date.today().isoformat() if today_str is None else today_str
                due_date = t.get("due")
                if due_date is None:
                    continue
                if not t["done"] and due_date < today:
                    filtered.append(t)
            else:
                filtered.append(t)
        tasks = filtered

    if not tasks:
        print("No tasks")
        return

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for t in tasks:
        print(format_task_line(t))


def cmd_done(args):
    if not args:
        print("Error: done requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: invalid ID {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_state(tasks)
    found["done"] = True
    save_data(tasks)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        print("Error: delete requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: invalid ID {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks = load_data()
    new_tasks = [t for t in tasks if t["id"] != task_id]

    if len(new_tasks) == len(tasks):
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_state(tasks)
    save_data(new_tasks)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        print("Error: edit requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: invalid ID {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts = args[i + 1:]
            new_title = " ".join(title_parts)
            break
        i += 1

    if new_title is None:
        print("Error: edit requires --title", file=sys.stderr)
        sys.exit(1)

    tasks = load_data()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break

    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    push_state(tasks)
    found["title"] = new_title
    save_data(tasks)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Error: search requires text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    tasks = load_data()
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task_line(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Error: --format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt not in ("json", "csv"):
        print("Error: --format must be json or csv", file=sys.stderr)
        sys.exit(1)

    tasks = load_data()
    tasks.sort(key=lambda t: t["id"])

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
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                tags_str, due_str))


def cmd_stats(args):
    tasks = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": undo,
}


def main():
    if len(sys.argv) < 2:
        print("Error: no command specified", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
