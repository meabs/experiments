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


def cmd_add(args):
    if not args:
        fail("Usage: add TITLE")
    title = " ".join(args)
    data = load()
    task_id = data["next_id"]
    data["next_id"] = task_id + 1
    data["tasks"].append({"id": task_id, "title": title, "done": False})
    save(data)
    print(f"Added {task_id}")


def task_line(t):
    mark = "x" if t.get("done") else " "
    return f"{t['id']} [{mark}] {t['title']}"


def cmd_list(args):
    if args:
        fail(f"Unexpected arguments: {' '.join(args)}")
    tasks = load()["tasks"]
    if not tasks:
        print("No tasks")
        return
    for t in sorted(tasks, key=lambda t: t["id"]):
        print(task_line(t))


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    data = load()
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            save(data)
            print(f"Done {task_id}")
            return
    fail(f"No such task: {task_id}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd, args = argv[0], argv[1:]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    COMMANDS[cmd](args)


if __name__ == "__main__":
    main(sys.argv[1:])
