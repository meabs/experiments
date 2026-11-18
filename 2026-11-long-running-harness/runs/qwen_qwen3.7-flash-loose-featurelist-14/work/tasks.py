#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
from copy import deepcopy
from datetime import date

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
    # Normalize task keys to integers for consistent lookup
    if isinstance(raw.get("tasks"), dict):
        new_tasks = {}
        for k, v in list(raw["tasks"].items()):
            new_tasks[int(k)] = v
        raw["tasks"] = new_tasks
    return raw


def save_data(data):
    serializable = {
        "tasks": {str(k): v for k, v in data["tasks"].items()},
        "next_id": data["next_id"],
        "history": data["history"],
    }
    with open(DATA_FILE, "w") as f:
        json.dump(serializable, f)


def push_history(data):
    """Save current state to history before a mutation."""
    data["history"].append({
        "tasks": deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    })


def pop_history(data):
    """Restore previous state from history."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]


def task_line(task):
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(tid), status, task["title"]]
    suffixes = []
    p = task.get("priority", "medium")
    if p != "medium":
        suffixes.append("(" + p + ")")
    for tag in task.get("tags", []):
        suffixes.append("#" + tag)
    if task.get("due"):
        suffixes.append("due:" + task["due"])
    parts.extend(suffixes)
    return " ".join(parts)


def validate_date(date_str):
    import calendar
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            raise ValueError
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        max_day = calendar.monthrange(year, month)[1]
        if month < 1 or month > 12 or day < 1 or day > max_day:
            raise ValueError
    except (ValueError, IndexError):
        print("Invalid date: " + date_str, file=sys.stderr)
        sys.exit(1)


def cmd_add(args, data):
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1
    if title is None:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: " + priority, file=sys.stderr)
        sys.exit(1)
    if due is not None:
        validate_date(due)
    push_history(data)
    nid = data["next_id"]
    data["tasks"][nid] = {
        "id": nid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = nid + 1
    save_data(data)
    print("Added " + str(nid))


def cmd_list(args, data):
    sort_by = None
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a date", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1
    if today is None:
        today = date.today().isoformat()
    tasks = list(data["tasks"].values())
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due") and t["due"] < today:
                filtered.append(t)
        tasks = filtered
    if sort_by == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (po.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: " + args[0], file=sys.stderr)
        sys.exit(1)
    if task_id not in data["tasks"]:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    data["tasks"][task_id]["done"] = True
    save_data(data)
    print("Done " + str(task_id))


def cmd_delete(args, data):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: " + args[0], file=sys.stderr)
        sys.exit(1)
    if task_id not in data["tasks"]:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    data["tasks"].pop(task_id)
    save_data(data)
    print("Deleted " + str(task_id))


def cmd_edit(args, data):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: " + args[0], file=sys.stderr)
        sys.exit(1)
    if task_id not in data["tasks"]:
        print("No such task: " + str(task_id), file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            new_title = args[i + 1]
            i += 2
        else:
            i += 1
    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    push_history(data)
    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print("Edited " + str(task_id))


def cmd_search(args, data):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"],
                "true" if t["done"] else "false",
                t["priority"], tags_str, due_str
            ))
    else:
        print("Invalid format: " + fmt, file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    tasks = data["tasks"].values()
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total))


def cmd_undo(args, data):
    pop_history(data)
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
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: " + command, file=sys.stderr)
        sys.exit(1)
    data = load_data()
    cmd_func = COMMANDS[command]
    cmd_func(sys.argv[2:], data)


if __name__ == "__main__":
    main()
