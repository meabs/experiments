#!/usr/bin/env python3
"""Command-line task manager. Data stored in tasks.json in the cwd."""
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


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {p: i for i, p in enumerate(PRIORITIES)}


def parse_options(args, valued, repeatable=()):
    """Split args into (positional, options). `valued` lists options taking a value.
    Options in `repeatable` collect all their values into a list."""
    positional, opts = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a in valued:
            if i + 1 >= len(args):
                fail(f"Missing value for {a}")
            if a in repeatable:
                opts.setdefault(a, []).append(args[i + 1])
            else:
                opts[a] = args[i + 1]
            i += 2
        else:
            positional.append(a)
            i += 1
    return positional, opts


def cmd_add(args):
    positional, opts = parse_options(args, ("--priority", "--tag"), ("--tag",))
    if not positional:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]...")
    title = " ".join(positional)
    priority = opts.get("--priority", "medium")
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = opts.get("--tag", [])
    data = load()
    task_id = data["next_id"]
    data["next_id"] = task_id + 1
    data["tasks"].append({"id": task_id, "title": title, "done": False,
                          "priority": priority, "tags": tags})
    save(data)
    print(f"Added {task_id}")


def format_task(t):
    mark = "x" if t.get("done") else " "
    line = f"{t['id']} [{mark}] {t['title']}"
    priority = t.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    for tag in t.get("tags", []):
        line += f" #{tag}"
    return line


def cmd_list(args):
    positional, opts = parse_options(args, ("--sort", "--tag"))
    if positional:
        fail(f"Unknown argument: {positional[0]}")
    sort = opts.get("--sort")
    if sort not in (None, "priority", "id"):
        fail(f"Invalid sort: {sort}")
    data = load()
    if not data["tasks"]:
        print("No tasks")
        return
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if "--tag" in opts:
        tasks = [t for t in tasks if opts["--tag"] in t.get("tags", [])]
        if not tasks:
            print("No tasks")
            return
    if sort == "priority":
        tasks.sort(key=lambda t: PRIORITY_RANK.get(t.get("priority", "medium"), 1))
    for t in tasks:
        print(format_task(t))


def cmd_done(args):
    if len(args) != 1 or not args[0].isdigit():
        fail("Usage: done ID")
    task_id = int(args[0])
    data = load()
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            save(data)
            print(f"Done {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_delete(args):
    if len(args) != 1 or not args[0].isdigit():
        fail("Usage: delete ID")
    task_id = int(args[0])
    data = load()
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            del data["tasks"][i]
            save(data)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd, args = argv[0], argv[1:]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    COMMANDS[cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
