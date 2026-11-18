#!/usr/bin/env python3
"""tasks.py - a small command-line task manager (stdlib only).

Data is stored in tasks.json in the current working directory.
Layout: {"next_id": <int>, "tasks": [{"id", "title", "done", ...}, ...]}
"""
import json
import os
import sys

DATA_FILE = "tasks.json"


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_opts(args, value_opts, flag_opts=()):
    """Split args into positionals and an options dict.

    value_opts: options taking one value (repeatable ones are collected in a list).
    Returns (positionals, opts) where opts maps option name (without --) to value(s).
    """
    positional = []
    opts = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in value_opts:
            name = a[2:]
            if i + 1 >= len(args):
                fail(f"Missing value for --{name}")
            opts.setdefault(name, []).append(args[i + 1])
            i += 2
        elif a.startswith("--") and a[2:] in flag_opts:
            opts[a[2:]] = True
            i += 1
        else:
            positional.append(a)
            i += 1
    return positional, opts


def cmd_add(args):
    positional, opts = parse_opts(args, ("priority", "tag"))
    if len(positional) != 1:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]...")
    title = positional[0]
    priority = opts.get("priority", ["medium"])[-1]
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    data = load()
    task_id = data["next_id"]
    data["tasks"].append({"id": task_id, "title": title, "done": False,
                          "priority": priority,
                          "tags": list(opts.get("tag", []))})
    data["next_id"] = task_id + 1
    save(data)
    print(f"Added {task_id}")


def task_line(t):
    mark = "x" if t.get("done") else " "
    line = f"{t['id']} [{mark}] {t['title']}"
    prio = t.get("priority", "medium")
    if prio != "medium":
        line += f" ({prio})"
    tags = t.get("tags") or []
    if tags:
        line += " " + " ".join(f"#{tag}" for tag in tags)
    return line


def cmd_list(args):
    positional, opts = parse_opts(args, ("sort", "tag"))
    if positional:
        fail(f"Unexpected arguments: {' '.join(positional)}")
    sort = opts.get("sort", [None])[-1]
    if sort not in (None, "priority"):
        fail(f"Invalid sort: {sort}")
    tasks = load()["tasks"]
    wanted = opts.get("tag", [])
    if wanted:
        tasks = [t for t in tasks if all(w in (t.get("tags") or []) for w in wanted)]
    if not tasks:
        print("No tasks")
        return
    if sort == "priority":
        key = lambda t: (PRIORITY_RANK.get(t.get("priority", "medium"), 1), t["id"])
    else:
        key = lambda t: t["id"]
    for t in sorted(tasks, key=key):
        print(task_line(t))


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def parse_id(value):
    try:
        return int(value)
    except ValueError:
        fail(f"Invalid id: {value}")


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    task_id = parse_id(args[0])
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    t["done"] = True
    save(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if len(args) != 1:
        fail("Usage: delete ID")
    task_id = parse_id(args[0])
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    data["tasks"].remove(t)
    save(data)
    print(f"Deleted {task_id}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
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
