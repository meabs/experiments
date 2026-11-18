#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date

DATA_FILE = "tasks.json"
UNDO_FILE = "tasks.undo.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"tasks": {}, "next_id": 1}
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo():
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def deep_copy(data):
    return json.loads(json.dumps(data))


KNOWN_FLAGS = {
    "--priority", "--tag", "--due", "--title", "--sort",
    "--overdue", "--today", "--format",
}


def parse_args(args):
    opts = {"_positional": [], "_flags": []}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            i += 1
            if i >= len(args):
                error("--priority requires a value")
            opts["priority"] = args[i]
        elif arg == "--tag":
            i += 1
            if i >= len(args):
                error("--tag requires a value")
            opts.setdefault("tags", []).append(args[i])
        elif arg == "--due":
            i += 1
            if i >= len(args):
                error("--due requires a value")
            opts["due"] = args[i]
        elif arg == "--title":
            # Collect all remaining positional arguments as title parts
            title_parts = []
            i += 1
            while i < len(args) and args[i] not in KNOWN_FLAGS:
                title_parts.append(args[i])
                i += 1
            opts["title"] = " ".join(title_parts)
            continue
        elif arg == "--sort":
            i += 1
            if i >= len(args):
                error("--sort requires a value")
            opts["sort"] = args[i]
        elif arg == "--overdue":
            opts["overdue"] = True
        elif arg == "--today":
            i += 1
            if i >= len(args):
                error("--today requires a value")
            opts["today"] = args[i]
        elif arg == "--format":
            i += 1
            if i >= len(args):
                error("--format requires a value")
            opts["format"] = args[i]
        elif arg.startswith("--"):
            error(f"Unknown option: {arg}")
        else:
            opts["_positional"].append(arg)
        i += 1
    return opts


def task_line(task):
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"
    if task["priority"] == "high":
        line += " (high)"
    elif task["priority"] == "low":
        line += " (low)"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def cmd_add(data, args):
    opts = parse_args(args)
    positional = opts.get("_positional", [])
    if not positional:
        error("Usage: add TITLE [--priority ...] [--tag ...] [--due ...]")
    title = positional[0]
    priority = opts.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")
    tags = opts.get("tags", [])
    due = opts.get("due", None)
    if due is not None:
        try:
            date.fromisoformat(due)
        except ValueError:
            error(f"Invalid date: {due}")
    history = load_undo()
    history.append({"type": "add", "data": deep_copy(data)})
    save_undo(history)
    task_id = data["next_id"]
    task_id_str = str(task_id)
    data["tasks"][task_id_str] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = task_id + 1
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(data, args):
    opts = parse_args(args)
    sort = opts.get("sort", None)
    tag_filter = opts.get("tags", None)
    overdue = opts.get("overdue", False)
    today_str = opts.get("today", None)
    if today_str:
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            error(f"Invalid date: {today_str}")
    else:
        today = date.today()
    tasks = list(data["tasks"].values())
    if tag_filter:
        tasks = [t for t in tasks if tag_filter[0] in t["tags"]]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t["due"] and date.fromisoformat(t["due"]) < today]
    if sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(data, args):
    opts = parse_args(args)
    positional = opts.get("_positional", [])
    if not positional:
        error("Usage: done ID")
    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"Invalid id: {positional[0]}")
    task_id_str = str(task_id)
    if task_id_str not in data["tasks"]:
        error(f"No such task: {task_id}")
    history = load_undo()
    history.append({"type": "done", "task_id": task_id, "data": deep_copy(data)})
    save_undo(history)
    data["tasks"][task_id_str]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(data, args):
    opts = parse_args(args)
    positional = opts.get("_positional", [])
    if not positional:
        error("Usage: delete ID")
    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"Invalid id: {positional[0]}")
    task_id_str = str(task_id)
    if task_id_str not in data["tasks"]:
        error(f"No such task: {task_id}")
    history = load_undo()
    history.append({
        "type": "delete",
        "task_id": task_id,
        "task": deep_copy(data["tasks"][task_id_str]),
        "data": deep_copy(data),
    })
    save_undo(history)
    del data["tasks"][task_id_str]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(data, args):
    opts = parse_args(args)
    positional = opts.get("_positional", [])
    if not positional:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(positional[0])
    except ValueError:
        error(f"Invalid id: {positional[0]}")
    task_id_str = str(task_id)
    if task_id_str not in data["tasks"]:
        error(f"No such task: {task_id}")
    if "title" not in opts:
        error("Usage: edit ID --title NEW TITLE")
    new_title = opts["title"]
    history = load_undo()
    history.append({
        "type": "edit",
        "task_id": task_id,
        "old_title": data["tasks"][task_id_str]["title"],
        "data": deep_copy(data),
    })
    save_undo(history)
    data["tasks"][task_id_str]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(data, args):
    opts = parse_args(args)
    positional = opts.get("_positional", [])
    if not positional:
        error("Usage: search TEXT")
    query = positional[0].lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(task_line(t))


def cmd_export(data, args):
    opts = parse_args(args)
    fmt = opts.get("format", None)
    if fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(data, args):
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(data, args):
    history = load_undo()
    if not history:
        error("Nothing to undo")
    entry = history.pop()
    save_undo(history)
    data = entry["data"]
    save_data(data)
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
    args = sys.argv[1:]
    if not args:
        error("Usage: python3 tasks.py <command> [args]")
    command = args[0]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    data = load_data()
    COMMANDS[command](data, args[1:])


if __name__ == "__main__":
    main()
