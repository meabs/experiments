#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid data format")
            data.setdefault("tasks", [])
            data.setdefault("next_id", 1)
            data.setdefault("undo_stack", [])
            return data
        except (json.JSONDecodeError, ValueError):
            pass
    return {"tasks": [], "next_id": 1, "undo_stack": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def push_undo(data):
    snapshot = {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }
    data["undo_stack"].append(snapshot)


def undo_cmd(data):
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    snapshot = data["undo_stack"].pop()
    data["tasks"] = snapshot["tasks"]
    data["next_id"] = snapshot["next_id"]
    save_data(data)
    print("Undone")


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def add_task(data, title, priority="medium", tags=None, due=None):
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)
    nid = data["next_id"]
    task = {
        "id": nid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags if tags else [],
        "due": due,
    }
    push_undo(data)
    data["tasks"].append(task)
    data["next_id"] = nid + 1
    save_data(data)
    print("Added {}".format(nid))


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    tid = task["id"]
    title = task["title"]
    line = "{} {} {}".format(tid, status, title)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    for tag in task.get("tags", []):
        line += " #{}".format(tag)
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def list_tasks(data, sort_priority=False, tag_filter=None, overdue=False, today=None):
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today is None:
            today = date.today().isoformat()
        else:
            try:
                datetime.strptime(today, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: {}".format(today), file=sys.stderr)
                sys.exit(1)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def done_task(data, task_id):
    task = find_task(data, task_id)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def delete_task(data, task_id):
    task = find_task(data, task_id)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def edit_task(data, task_id, new_title):
    task = find_task(data, task_id)
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(data)
    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def search_tasks(data, text):
    matches = [t for t in data["tasks"] if text.lower() in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in sorted(matches, key=lambda t: t["id"]):
        print(format_task_line(task))


def export_tasks(data, fmt):
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for task in tasks:
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in tasks:
            writer.writerow([
                task["id"],
                task["title"],
                "true" if task["done"] else "false",
                task["priority"],
                ";".join(task.get("tags", [])),
                task.get("due") or "",
            ])
        print(buf.getvalue(), end="")


def stats(data):
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def parse_args(args):
    """Parse command-line arguments into command name and options."""
    if not args:
        return None, {}

    cmd = args[0]
    opts = {"_positional": []}
    i = 1
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg.lstrip("-")
            if key in ("tag",) and key not in opts:
                opts[key] = []
            if key in ("tag", "title"):
                # Collect remaining positional args until next --flag
                i += 1
                values = []
                while i < len(args) and not args[i].startswith("--"):
                    values.append(args[i])
                    i += 1
                if key == "tag":
                    for v in values:
                        opts[key].append(v)
                else:
                    opts["title_rest"] = values
            else:
                i += 1
                if i < len(args) and not args[i].startswith("--"):
                    opts[key] = args[i]
                else:
                    opts[key] = True
        else:
            opts["_positional"].append(arg)
        i += 1
    return cmd, opts


def main():
    args = sys.argv[1:]
    cmd, opts = parse_args(args)

    if cmd is None:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    data = load_data()

    if cmd == "add":
        pos = opts.get("_positional", [])
        title_parts = pos
        if "title_rest" in opts:
            title_parts = opts["title_rest"]
        if not title_parts:
            print("Missing title", file=sys.stderr)
            sys.exit(1)
        title = " ".join(title_parts)
        priority = opts.get("priority", "medium")
        tags = opts.get("tag", [])
        due = opts.get("due", None)
        add_task(data, title, priority, tags, due)

    elif cmd == "list":
        sort_priority = opts.get("sort") == "priority"
        tag_filter = opts.get("tag", None)
        overdue = "overdue" in opts
        today = opts.get("today", None)
        list_tasks(data, sort_priority=sort_priority, tag_filter=tag_filter,
                   overdue=overdue, today=today)

    elif cmd == "done":
        pos = opts.get("_positional", [])
        if not pos:
            print("Missing task id", file=sys.stderr)
            sys.exit(1)
        try:
            task_id = int(pos[0])
        except ValueError:
            print("Invalid task id: {}".format(pos[0]), file=sys.stderr)
            sys.exit(1)
        done_task(data, task_id)

    elif cmd == "delete":
        pos = opts.get("_positional", [])
        if not pos:
            print("Missing task id", file=sys.stderr)
            sys.exit(1)
        try:
            task_id = int(pos[0])
        except ValueError:
            print("Invalid task id: {}".format(pos[0]), file=sys.stderr)
            sys.exit(1)
        delete_task(data, task_id)

    elif cmd == "edit":
        pos = opts.get("_positional", [])
        if not pos:
            print("Missing task id", file=sys.stderr)
            sys.exit(1)
        try:
            task_id = int(pos[0])
        except ValueError:
            print("Invalid task id: {}".format(pos[0]), file=sys.stderr)
            sys.exit(1)
        title_rest = opts.get("title_rest", [])
        if not title_rest:
            print("Missing new title", file=sys.stderr)
            sys.exit(1)
        new_title = " ".join(title_rest)
        edit_task(data, task_id, new_title)

    elif cmd == "search":
        pos = opts.get("_positional", [])
        if not pos:
            print("Missing search text", file=sys.stderr)
            sys.exit(1)
        search_text = " ".join(pos)
        search_tasks(data, search_text)

    elif cmd == "export":
        fmt = opts.get("format", None)
        if fmt is None:
            print("Missing format", file=sys.stderr)
            sys.exit(1)
        if fmt not in ("json", "csv"):
            print("Invalid format: {}".format(fmt), file=sys.stderr)
            sys.exit(1)
        export_tasks(data, fmt)

    elif cmd == "stats":
        stats(data)

    elif cmd == "undo":
        undo_cmd(data)

    else:
        print("Unknown command: {}".format(cmd), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
