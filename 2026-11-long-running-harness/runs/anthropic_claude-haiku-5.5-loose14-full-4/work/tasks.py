#!/usr/bin/env python3
"""Command-line task manager. Data is stored in tasks.json in the cwd."""
import datetime
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def record(data):
    """Push a snapshot of the current state onto the undo history."""
    data.setdefault("history", []).append(
        {"next_id": data["next_id"], "tasks": json.loads(json.dumps(data["tasks"]))})


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fail(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_opts(args, flags):
    """Split args into positionals and a dict of option values.

    flags maps option name -> True if it may repeat (value is a list),
    False for a single value, or "flag" for a boolean switch with no value.
    """
    positional = []
    opts = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in flags:
            name = a[2:]
            if flags[name] == "flag":
                opts[name] = True
                i += 1
                continue
            if i + 1 >= len(args):
                fail(f"Missing value for {a}")
            value = args[i + 1]
            if flags[name]:
                opts.setdefault(name, []).append(value)
            else:
                opts[name] = value
            i += 2
        else:
            positional.append(a)
            i += 1
    return positional, opts


def parse_date(value):
    """Return the validated YYYY-MM-DD string, or fail."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        fail(f"Invalid date: {value}")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        fail(f"Invalid date: {value}")
    return value


def cmd_add(args):
    positional, opts = parse_opts(args, {"priority": False, "tag": True, "due": False})
    if not positional:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = positional[0]
    priority = opts.get("priority", "medium")
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    due = parse_date(opts["due"]) if "due" in opts else None
    data = load()
    record(data)
    task_id = data["next_id"]
    tags = list(opts.get("tag", []))
    data["tasks"].append({"id": task_id, "title": title, "done": False,
                          "priority": priority, "tags": tags, "due": due})
    data["next_id"] = task_id + 1
    save(data)
    print(f"Added {task_id}")


def format_line(task):
    mark = "x" if task["done"] else " "
    line = f"{task['id']} [{mark}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_list(args):
    positional, opts = parse_opts(args, {"sort": False, "tag": False,
                                         "overdue": "flag", "today": False})
    data = load()
    if not data["tasks"]:
        print("No tasks")
        return
    tasks = list(data["tasks"])
    tag = opts.get("tag")
    if tag is not None:
        tasks = [t for t in tasks if tag in t.get("tags", [])]
    if opts.get("overdue"):
        today = parse_date(opts["today"]) if "today" in opts else datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    sort = opts.get("sort")
    if sort == "priority":
        tasks.sort(key=lambda t: (PRIORITY_RANK[t.get("priority", "medium")], t["id"]))
    elif sort is not None:
        fail(f"Invalid sort: {sort}")
    for task in tasks:
        print(format_line(task))


def cmd_done(args):
    if not args:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    data = load()
    for task in data["tasks"]:
        if task["id"] == task_id:
            record(data)
            task["done"] = True
            save(data)
            print(f"Done {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_delete(args):
    if not args:
        fail("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    data = load()
    for task in data["tasks"]:
        if task["id"] == task_id:
            record(data)
            data["tasks"].remove(task)
            save(data)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_edit(args):
    if not args:
        fail("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    rest = args[1:]
    if not rest or rest[0] != "--title" or len(rest) < 2:
        fail("Usage: edit ID --title NEW TITLE")
    new_title = " ".join(rest[1:])
    data = load()
    for task in data["tasks"]:
        if task["id"] == task_id:
            record(data)
            task["title"] = new_title
            save(data)
            print(f"Edited {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_search(args):
    if not args:
        fail("Usage: search TEXT")
    needle = " ".join(args).lower()
    data = load()
    matches = [t for t in data["tasks"] if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_line(task))


def cmd_export(args):
    positional, opts = parse_opts(args, {"format": False})
    fmt = opts.get("format")
    if fmt not in ("json", "csv"):
        fail("Usage: export --format json|csv")
    tasks = load()["tasks"]
    if fmt == "json":
        out = [{"id": t["id"], "title": t["title"], "done": bool(t["done"]),
                "priority": t.get("priority", "medium"), "tags": list(t.get("tags", [])),
                "due": t.get("due") or None} for t in tasks]
        print(json.dumps(out, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for t in tasks:
        row = [str(t["id"]), t["title"], "true" if t["done"] else "false",
               t.get("priority", "medium"), ";".join(t.get("tags", [])),
               t.get("due") or ""]
        print(",".join(row))


def cmd_stats(args):
    tasks = load()["tasks"]
    done = sum(1 for t in tasks if t["done"])
    print(f"open: {len(tasks) - done}")
    print(f"done: {done}")
    print(f"total: {len(tasks)}")


def cmd_undo(args):
    data = load()
    history = data.get("history", [])
    if not history:
        fail("Nothing to undo")
    prev = history.pop()
    data["next_id"] = prev["next_id"]
    data["tasks"] = prev["tasks"]
    save(data)
    print("Undone")


COMMANDS = {
    "undo": cmd_undo,
    "search": cmd_search,
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd = argv[0]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
