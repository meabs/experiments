#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import copy
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
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(state):
    history = load_history()
    history.append(copy.deepcopy(state))
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        return None
    state = history.pop()
    save_history(history)
    return state


def next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def format_task(task):
    done_marker = "[x]" if task.get("done", False) else "[ ]"
    line = "{} {} {}".format(task["id"], done_marker, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    title = " ".join(args.title)
    priority = args.priority if args.priority else "medium"
    tags = args.tag if args.tag else []
    due = getattr(args, "due", None) or None

    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)

    if due is not None:
        if not validate_date(due):
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)

    tasks = load_tasks()
    push_history(tasks)
    new_id = next_id(tasks)
    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print("Added {}".format(new_id))


def cmd_list(args):
    tasks = load_tasks()

    if args.tag:
        filter_tag = args.tag[0] if isinstance(args.tag, list) else args.tag
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if args.overdue:
        today_str = args.today if args.today else date.today().strftime("%Y-%m-%d")
        if not validate_date(today_str):
            print("Invalid date: {}".format(today_str), file=sys.stderr)
            sys.exit(1)
        filtered = []
        for t in tasks:
            if t.get("due") and not t.get("done", False):
                if t["due"] < today_str:
                    filtered.append(t)
        tasks = filtered

    if not tasks:
        print("No tasks")
        return

    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for t in tasks:
        print(format_task(t))


def cmd_done(args):
    task_id = args.id
    tasks = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(tasks)
    found["done"] = True
    save_tasks(tasks)
    print("Done {}".format(task_id))


def cmd_delete(args):
    task_id = args.id
    tasks = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    task_id = args.id
    tasks = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if found is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(tasks)
    title_parts = args.title
    if title_parts:
        found["title"] = " ".join(title_parts)
    save_tasks(tasks)
    print("Edited {}".format(task_id))


def cmd_search(args):
    tasks = load_tasks()
    text = " ".join(args.text).lower()
    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task(t))


def cmd_export(args):
    fmt = args.format
    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t.get("done", False),
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t.get("done", False) else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue(), end="")
    else:
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t.get("done", False))
    done_count = sum(1 for t in tasks if t.get("done", False))
    total_count = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


def cmd_undo(args):
    state = pop_history()
    if state is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    save_tasks(state)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority")
    add_parser.add_argument("--tag", action="append")
    add_parser.add_argument("--due")

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", choices=["priority"])
    list_parser.add_argument("--tag")
    list_parser.add_argument("--overdue", action="store_true")
    list_parser.add_argument("--today")

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    # delete
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)

    # edit
    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("--title", nargs="+")

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text", nargs="+")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", required=True, choices=["json", "csv"])

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

    if args.command is None:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

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

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        print("Unknown command: {}".format(args.command), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
