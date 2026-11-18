#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(tasks, next_id):
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_undo_history(history)


def pop_undo():
    history = load_undo_history()
    if not history:
        return None
    state = history.pop()
    save_undo_history(history)
    return state["tasks"], state["next_id"]


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = str(task["id"]) + " " + status + " " + task["title"]
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#" + t for t in tags)
    due = task.get("due")
    if due:
        line += " due:" + due
    return line


def validate_date(date_str):
    try:
        d = date.fromisoformat(date_str)
        return True
    except (ValueError, TypeError):
        return False


def parse_args(argv):
    positional = []
    opts = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            key = arg[2:]
            if key == "tag":
                i += 1
                if i < len(argv):
                    opts.setdefault("tags", []).append(argv[i])
                i += 1
            elif key == "title":
                i += 1
                parts = []
                while i < len(argv) and not argv[i].startswith("--"):
                    parts.append(argv[i])
                    i += 1
                if parts:
                    opts["new_title"] = " ".join(parts)
                else:
                    opts["new_title"] = ""
            elif key == "today":
                i += 1
                if i < len(argv):
                    opts["today"] = argv[i]
                i += 1
            elif key in ("sort", "priority", "due", "format"):
                i += 1
                if i < len(argv) and not argv[i].startswith("--"):
                    opts[key] = argv[i]
                i += 1
            elif key in ("overdue",):
                opts[key] = True
                i += 1
            else:
                i += 1
                if i < len(argv) and not argv[i].startswith("--"):
                    opts[key] = argv[i]
                    i += 1
                else:
                    opts[key] = True
        else:
            positional.append(arg)
            i += 1
    return positional, opts


def cmd_add(tasks, next_id, opts, positional):
    if not positional:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(positional)
    priority = opts.get("priority", "medium")
    tags = opts.get("tags", [])
    due = opts.get("due", None)
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: " + priority, file=sys.stderr)
        sys.exit(1)
    if due is not None:
        if not validate_date(due):
            print("Invalid date: " + due, file=sys.stderr)
            sys.exit(1)
    push_undo(tasks, next_id)
    new_id = next_id
    task = {
        "id": new_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print("Added " + str(new_id))


def cmd_list(tasks, next_id, opts, positional):
    sort = opts.get("sort", None)
    tag_filter = opts.get("tag", None)
    overdue = opts.get("overdue", False)
    today_str = opts.get("today", None)
    filtered = list(tasks)
    if tag_filter is not None:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]
    if overdue:
        if today_str is not None:
            if not validate_date(today_str):
                print("Invalid date: " + today_str, file=sys.stderr)
                sys.exit(1)
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        filtered = [
            t for t in filtered
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today
        ]
    if sort == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (prio_order.get(t["priority"], 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])
    if not filtered:
        print("No tasks")
    else:
        for task in filtered:
            print(task_line(task))


def cmd_done(tasks, next_id, opts, positional):
    if not positional:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("No such task: " + positional[0], file=sys.stderr)
        sys.exit(1)
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    task["done"] = True
    save_tasks(tasks, next_id)
    print("Done " + str(task_id))


def cmd_delete(tasks, next_id, opts, positional):
    if not positional:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("No such task: " + positional[0], file=sys.stderr)
        sys.exit(1)
    task = None
    idx = None
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            task = t
            idx = i
            break
    if task is None:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks.pop(idx)
    save_tasks(tasks, next_id)
    print("Deleted " + str(task_id))


def cmd_edit(tasks, next_id, opts, positional):
    if not positional:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("No such task: " + positional[0], file=sys.stderr)
        sys.exit(1)
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)
    new_title = opts.get("new_title", None)
    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    task["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited " + str(task_id))


def cmd_search(tasks, next_id, opts, positional):
    if not positional:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(positional).lower()
    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(tasks, next_id, opts, positional):
    fmt = opts.get("format", "json")
    tasks_sorted = sorted(tasks, key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in tasks_sorted:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks_sorted:
            tags_str = ";".join(t.get("tags", []))
            due_val = t.get("due", "") or ""
            done_val = "true" if t["done"] else "false"
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_val,
                t.get("priority", "medium"), tags_str, due_val))
    else:
        print("Invalid format: " + fmt, file=sys.stderr)
        sys.exit(1)


def cmd_stats(tasks, next_id, opts, positional):
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total_count))


def cmd_undo(tasks, next_id, opts, positional):
    result = pop_undo()
    if result is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    saved_tasks, saved_next_id = result
    # Don't push current state before undoing - undo only reverts last mutation
    save_tasks(saved_tasks, saved_next_id)
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
        print("Unknown command: " + command, file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    positional, opts = parse_args(sys.argv[2:])
    COMMANDS[command](tasks, next_id, opts, positional)


if __name__ == "__main__":
    main()
