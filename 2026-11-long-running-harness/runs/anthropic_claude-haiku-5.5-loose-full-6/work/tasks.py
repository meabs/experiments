#!/usr/bin/env python3
"""tasks.py - a small command-line task manager (stdlib only)."""
import argparse
import json
import os
import sys

DATA_FILE = "tasks.json"


class TaskError(Exception):
    pass


def load_store(path=DATA_FILE):
    """Return the store dict: {"next_id": int, "tasks": [task, ...]}."""
    if not os.path.exists(path):
        return {"next_id": 1, "tasks": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_store(store, path=DATA_FILE):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)
    os.replace(tmp, path)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def cmd_add(args):
    priority = args.priority
    if priority not in PRIORITIES:
        raise TaskError(f"Invalid priority: {priority}")
    store = load_store()
    task_id = store["next_id"]
    store["next_id"] = task_id + 1
    tags = list(args.tag or [])
    store["tasks"].append({"id": task_id, "title": args.title, "done": False,
                           "priority": priority, "tags": tags})
    save_store(store)
    print(f"Added {task_id}")


def format_task(task):
    """Format a task line: '<id> [ ] <title>' or '<id> [x] <title>'."""
    mark = "x" if task.get("done") else " "
    line = f"{task['id']} [{mark}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    tags = task.get("tags") or []
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    return line


def cmd_list(args):
    store = load_store()
    if not store["tasks"]:
        print("No tasks")
        return
    tasks = sorted(store["tasks"], key=lambda t: t["id"])
    if args.tag:
        tasks = [t for t in tasks if args.tag in (t.get("tags") or [])]
    if args.sort == "priority":
        tasks = sorted(tasks, key=lambda t: PRIORITY_RANK.get(t.get("priority", "medium"), 1))
    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    store = load_store()
    for task in store["tasks"]:
        if task["id"] == args.id:
            task["done"] = True
            save_store(store)
            print(f"Done {args.id}")
            return
    raise TaskError(f"No such task: {args.id}")


def cmd_delete(args):
    store = load_store()
    for i, task in enumerate(store["tasks"]):
        if task["id"] == args.id:
            del store["tasks"][i]
            save_store(store)
            print(f"Deleted {args.id}")
            return
    raise TaskError(f"No such task: {args.id}")


def build_parser():
    parser = argparse.ArgumentParser(prog="tasks.py", description="Command-line task manager.")
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--tag", action="append", default=None)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--sort", choices=["id", "priority"], default="id")
    p_list.add_argument("--tag", default=None)
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)

    p_delete = sub.add_parser("delete", help="delete a task")
    p_delete.add_argument("id", type=int)
    p_delete.set_defaults(func=cmd_delete)
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        args.func(args)
    except TaskError as e:
        print(str(e), file=sys.stderr)
        return 1
    except SystemExit as e:
        # argparse exits with 2 on usage errors; the spec requires 1 for any error.
        if e.code not in (0, None):
            return 1
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
