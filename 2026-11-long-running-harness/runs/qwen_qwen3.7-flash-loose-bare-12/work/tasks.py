#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import copy
import csv
import io
import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "next_id": 1}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


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
        json.dump(history, f)


def push_history(data):
    history = load_history()
    history.append(copy.deepcopy(data))
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        return None
    prev_data = history.pop()
    save_history(history)
    return prev_data


def parse_date(value):
    try:
        parts = value.split("-")
        if len(parts) != 3:
            return None
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)
    except (ValueError, TypeError):
        return None


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    # Priority suffix: only high and low shown, medium is implicit
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    # Due date suffix
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def cmd_add(args):
    data = load_data()
    push_history(data)
    title = " ".join(args.title)
    priority = args.priority
    tags = args.tag if args.tag else []
    due = args.due
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)
    if due:
        parsed = parse_date(due)
        if parsed is None:
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)
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
    print("Added {}".format(task["id"]))


def cmd_list(args):
    data = load_data()
    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return
    result = list(tasks)
    # Filter by tag - show tasks that have at least one of the specified tags
    if args.tag:
        req_tags = set(args.tag)
        result = [t for t in result if req_tags.intersection(set(t.get("tags", [])))]
    # Overdue filter
    if args.overdue:
        today_str = args.today
        if today_str:
            today = parse_date(today_str)
            if today is None:
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()
        filtered = []
        for t in result:
            if not t["done"] and t.get("due"):
                due_date = parse_date(t["due"])
                if due_date and due_date < today:
                    filtered.append(t)
        result = filtered
    # Sort by priority or id
    if args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        result.sort(key=lambda t: t["id"])
    if not result:
        print("No tasks")
        return
    for task in result:
        print(format_task_line(task))


def cmd_done(args):
    data = load_data()
    task_id = args.id
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(args):
    data = load_data()
    task_id = args.id
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    data = load_data()
    task_id = args.id
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    task["title"] = " ".join(args.title)
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(args):
    data = load_data()
    query = args.text.lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    fmt = args.format
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due") or "",
            ])
        print(buf.getvalue(), end="")
    else:
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


def cmd_undo(args):
    prev_data = pop_history()
    if prev_data is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    save_data(prev_data)
    print("Undone")


def build_parser():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--tag", action="append", default=None)
    p_add.add_argument("--due", default=None)

    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", choices=["priority"], default=None)
    p_list.add_argument("--tag", action="append", default=None)
    p_list.add_argument("--overdue", action="store_true", default=False)
    p_list.add_argument("--today", default=None)

    # done
    p_done = subparsers.add_parser("done")
    p_done.add_argument("id", type=int)

    # delete
    p_delete = subparsers.add_parser("delete")
    p_delete.add_argument("id", type=int)

    # edit
    p_edit = subparsers.add_parser("edit")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+", required=True)

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("text")

    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("--format", required=True)

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help(file=sys.stderr)
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
        parser.print_help(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
