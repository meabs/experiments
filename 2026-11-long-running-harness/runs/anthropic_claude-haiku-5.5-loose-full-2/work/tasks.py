#!/usr/bin/env python3
"""Command-line task manager. Stores data in tasks.json in the cwd."""
import json
import os
import sys

DATA_FILE = "tasks.json"


def load_state():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_opts(args, options):
    """Split args into positionals and --opt value pairs.

    options: set of option names (without --). Returns (positionals, dict of name -> list of values).
    """
    positional = []
    opts = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in options:
            name = a[2:]
            if i + 1 >= len(args):
                fail(f"Missing value for --{name}")
            opts.setdefault(name, []).append(args[i + 1])
            i += 2
        else:
            positional.append(a)
            i += 1
    return positional, opts


def cmd_add(args):
    pos, opts = parse_opts(args, {"priority", "tag"})
    if len(pos) != 1:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]...")
    title = pos[0]
    priority = opts.get("priority", ["medium"])[-1]
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = opts.get("tag", [])
    state = load_state()
    task_id = state["next_id"]
    state["tasks"].append({"id": task_id, "title": title, "done": False,
                           "priority": priority, "tags": tags})
    state["next_id"] = task_id + 1
    save_state(state)
    print(f"Added {task_id}")


def format_line(task):
    mark = "x" if task.get("done") else " "
    line = f"{task['id']} [{mark}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    return line


def cmd_list(args):
    pos, opts = parse_opts(args, {"sort", "tag"})
    if pos:
        fail(f"Unexpected arguments: {' '.join(pos)}")
    sort = opts.get("sort", [None])[-1]
    if sort not in (None, "priority"):
        fail(f"Invalid sort: {sort}")
    tag = opts.get("tag", [None])[-1]
    tasks = sorted(load_state()["tasks"], key=lambda t: t["id"])
    if tag is not None:
        tasks = [t for t in tasks if tag in t.get("tags", [])]
    if sort == "priority":
        tasks.sort(key=lambda t: PRIORITY_RANK.get(t.get("priority", "medium"), 1))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_line(task))


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    state = load_state()
    for task in state["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            save_state(state)
            print(f"Done {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_delete(args):
    if len(args) != 1:
        fail("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    state = load_state()
    for i, task in enumerate(state["tasks"]):
        if task["id"] == task_id:
            del state["tasks"][i]
            save_state(state)
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
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        fail(f"Unknown command: {argv[0]}")
    cmd(argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
