#!/usr/bin/env python3
"""Command-line task manager. Stores data in tasks.json in the cwd."""
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


def cmd_add(args):
    priority = "medium"
    tags = []
    words = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                fail("Usage: add TITLE [--priority high|medium|low]")
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                fail("Usage: add TITLE [--tag TAG]")
            tags.append(args[i + 1])
            i += 2
        else:
            words.append(args[i])
            i += 1
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    if not words:
        fail("Usage: add TITLE")
    title = " ".join(words)
    data = load()
    task_id = data["next_id"]
    data["tasks"].append({"id": task_id, "title": title, "done": False,
                          "priority": priority, "tags": tags})
    data["next_id"] = task_id + 1
    save(data)
    print(f"Added {task_id}")


def task_line(t):
    mark = "x" if t.get("done") else " "
    line = f"{t['id']} [{mark}] {t['title']}"
    pri = t.get("priority", "medium")
    if pri != "medium":
        line += f" ({pri})"
    for tag in t.get("tags", []):
        line += f" #{tag}"
    return line


def cmd_list(args):
    sort = None
    tag = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort = "priority"
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag = args[i + 1]
            i += 2
        else:
            fail(f"Unknown option: {args[i]}")
    tasks = load()["tasks"]
    if not tasks:
        print("No tasks")
        return
    tasks = sorted(tasks, key=lambda t: t["id"])
    if tag is not None:
        tasks = [t for t in tasks if tag in t.get("tags", [])]
        if not tasks:
            print("No tasks")
            return
    if sort == "priority":
        rank = {p: n for n, p in enumerate(PRIORITIES)}
        tasks = sorted(tasks, key=lambda t: rank.get(t.get("priority", "medium"), 1))
    for t in tasks:
        print(task_line(t))


def find_task(data, task_id_str):
    try:
        task_id = int(task_id_str)
    except ValueError:
        fail(f"No such task: {task_id_str}")
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    fail(f"No such task: {task_id_str}")


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    data = load()
    t = find_task(data, args[0])
    t["done"] = True
    save(data)
    print(f"Done {t['id']}")


def cmd_delete(args):
    if len(args) != 1:
        fail("Usage: delete ID")
    data = load()
    t = find_task(data, args[0])
    data["tasks"].remove(t)
    save(data)
    print(f"Deleted {t['id']}")


COMMANDS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        fail(f"Unknown command: {argv[0]}")
    cmd(argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
