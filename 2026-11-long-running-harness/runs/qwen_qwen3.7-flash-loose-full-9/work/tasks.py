#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    raw_tasks = data.get("tasks", {})
    tasks = {int(k): v for k, v in raw_tasks.items()}
    return tasks, data.get("next_id", 1)


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f, indent=2)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_undo(tasks, next_id):
    history = load_undo()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_undo(history)


def pop_undo():
    history = load_undo()
    if not history:
        return None
    state = history.pop()
    save_undo(history)
    return state["tasks"], state["next_id"]


def format_task_line(task):
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(tid, status, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join("#{}".format(tag) for tag in task["tags"])
    if task.get("due"):
        line += " due:{}".format(task["due"])
    return line


def cmd_add(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i]
            try:
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError("bad format")
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if month < 1 or month > 12:
                    raise ValueError("bad month")
                if day < 1 or day > 31:
                    raise ValueError("bad day")
                import calendar
                max_day = calendar.monthrange(year, month)[1]
                if day > max_day:
                    raise ValueError("bad day for month")
            except (ValueError, IndexError):
                print("Invalid date: {}".format(due), file=sys.stderr)
                sys.exit(1)
        else:
            title_parts.append(arg)
        i += 1
    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)
    task_id = next_id
    tasks[task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_tasks(tasks, next_id + 1)
    print("Added {}".format(task_id))


def cmd_list(args):
    tasks, _ = load_tasks()
    tag_filter = None
    sort_by = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--tag":
            i += 1
            if i >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i]
        elif arg == "--sort":
            i += 1
            if i >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                print("Missing date value", file=sys.stderr)
                sys.exit(1)
            today = args[i]
        else:
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)
        i += 1
    filtered = list(tasks.values())
    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]
    if overdue:
        if today is None:
            from datetime import date
            today = date.today().isoformat()
        filtered = [t for t in filtered if not t["done"] and t.get("due") and t["due"] < today]
    if sort_by == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    elif sort_by:
        print("Unknown sort option: {}".format(sort_by), file=sys.stderr)
        sys.exit(1)
    else:
        filtered.sort(key=lambda t: t["id"])
    if not filtered:
        print("No tasks")
    else:
        for task in filtered:
            print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            title_parts = []
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks.values() if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            i += 1
            if i >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i]
        i += 1
    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)
    tasks, _ = load_tasks()
    sorted_tasks = sorted(tasks.values(), key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in sorted_tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in sorted_tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            print("{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t.get("priority", "medium"), tags_str, due_str))
    else:
        print("Unknown format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, _ = load_tasks()
    total = len(tasks)
    done_count = sum(1 for t in tasks.values() if t["done"])
    open_count = total - done_count
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    result = pop_undo()
    if result is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = result
    # Write empty tasks.json since we just popped state
    save_tasks(tasks, next_id)
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
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
