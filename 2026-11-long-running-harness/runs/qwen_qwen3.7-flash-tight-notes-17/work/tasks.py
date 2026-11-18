#!/usr/bin/env python3
"""A command-line task manager."""
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


def load_data():
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE) as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_data(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f, indent=2)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    # Priority suffix (high or low only; medium has no suffix)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    # Due date suffix
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def find_task(tasks, task_id):
    for t in tasks:
        if t["id"] == task_id:
            return t
    return None


def cmd_add(args):
    title = " ".join(args.title)
    priority = args.priority
    tags = args.tag if args.tag else []
    due = args.due

    # Validate priority manually (not via argparse choices)
    valid_priorities = ["high", "medium", "low"]
    if priority not in valid_priorities:
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)

    # Validate date if provided
    if due is not None and not validate_date(due):
        print("Invalid date: {}".format(due), file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_data()
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Record history for undo
    history = load_history()
    history.append({"action": "add", "task": copy.deepcopy(task)})
    save_history(history)

    tasks.append(task)
    save_data(tasks, next_id + 1)
    print("Added {}".format(task["id"]))


def cmd_list(args):
    tasks, _ = load_data()
    if not tasks:
        print("No tasks")
        return

    filtered = list(tasks)

    # Filter by tag if specified
    if args.tag is not None:
        filtered = [t for t in filtered if args.tag in t.get("tags", [])]

    # Filter overdue tasks if specified
    if args.overdue:
        today_str = args.today if args.today else date.today().isoformat()
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date: {}".format(today_str), file=sys.stderr)
            sys.exit(1)
        today_str = today.isoformat()
        filtered = [
            t
            for t in filtered
            if not t["done"]
            and t.get("due")
            and t["due"] < today_str
        ]

    # Sort if requested
    if args.sort == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for task in filtered:
        print(format_task_line(task))


def cmd_done(args):
    tasks, next_id = load_data()
    task = find_task(tasks, args.id)
    if task is None:
        print("No such task: {}".format(args.id), file=sys.stderr)
        sys.exit(1)

    # Record history for undo
    history = load_history()
    history.append(
        {"action": "done", "task_id": args.id, "old_done": task["done"]}
    )
    save_history(history)

    task["done"] = True
    save_data(tasks, next_id)
    print("Done {}".format(args.id))


def cmd_delete(args):
    tasks, next_id = load_data()
    task = find_task(tasks, args.id)
    if task is None:
        print("No such task: {}".format(args.id), file=sys.stderr)
        sys.exit(1)

    # Record history for undo
    history = load_history()
    history.append({"action": "delete", "task": copy.deepcopy(task)})
    save_history(history)

    tasks = [t for t in tasks if t["id"] != args.id]
    save_data(tasks, next_id)
    print("Deleted {}".format(args.id))


def cmd_edit(args):
    tasks, next_id = load_data()
    task = find_task(tasks, args.id)
    if task is None:
        print("No such task: {}".format(args.id), file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(args.new_title)

    # Record history for undo
    history = load_history()
    history.append(
        {"action": "edit", "task_id": args.id, "old_title": task["title"]}
    )
    save_history(history)

    task["title"] = new_title
    save_data(tasks, next_id)
    print("Edited {}".format(args.id))


def cmd_search(args):
    tasks, _ = load_data()
    query = " ".join(args.text).lower()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    tasks, _ = load_data()
    tasks.sort(key=lambda t: t["id"])
    if args.fmt == "json":
        output = []
        for t in tasks:
            output.append(
                {
                    "id": t["id"],
                    "title": t["title"],
                    "done": t["done"],
                    "priority": t.get("priority", "medium"),
                    "tags": t.get("tags", []),
                    "due": t.get("due"),
                }
            )
        print(json.dumps(output, indent=2))
    elif args.fmt == "csv":
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            w.writerow(
                [
                    t["id"],
                    t["title"],
                    str(t["done"]).lower(),
                    t.get("priority", "medium"),
                    ";".join(t.get("tags", [])),
                    t["due"] if t.get("due") else "",
                ]
            )
        print(out.getvalue(), end="")


def cmd_stats(args):
    tasks, _ = load_data()
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    print("open: {}".format(total - done_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    entry = history.pop()
    tasks, next_id = load_data()

    if entry["action"] == "add":
        # Remove the added task
        tasks = [t for t in tasks if t["id"] != entry["task"]["id"]]
        # Restore next_id to what it was before the add
        next_id = entry["task"]["id"]
    elif entry["action"] == "done":
        task = find_task(tasks, entry["task_id"])
        if task:
            task["done"] = entry["old_done"]
    elif entry["action"] == "delete":
        # Restore the deleted task
        tasks.append(entry["task"])
    elif entry["action"] == "edit":
        task = find_task(tasks, entry["task_id"])
        if task:
            task["title"] = entry["old_title"]

    save_data(tasks, next_id)
    save_history(history)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--tag", action="append", default=None)
    p_add.add_argument("--due", default=None)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--sort", default=None)
    p_list.add_argument("--tag", default=None)
    p_list.add_argument("--overdue", action="store_true", default=False)
    p_list.add_argument("--today", default=None)

    # done
    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)

    # delete
    p_del = sub.add_parser("delete")
    p_del.add_argument("id", type=int)

    # edit
    p_edit = sub.add_parser("edit")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+", required=True)

    # search
    p_search = sub.add_parser("search")
    p_search.add_argument("text", nargs="+")

    # export
    p_export = sub.add_parser("export")
    p_export.add_argument("--format", choices=["json", "csv"], required=True, dest="fmt")

    # stats
    sub.add_parser("stats")

    # undo
    sub.add_parser("undo")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
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
    commands[args.command](args)


if __name__ == "__main__":
    main()
