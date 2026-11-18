#!/usr/bin/env python3
"""Command-line task manager (see SPEC.md)."""
import argparse
import copy
import datetime
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


def load_state():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def record(state):
    """Push a snapshot of the mutable state onto the undo history."""
    state.setdefault("history", []).append(
        {"tasks": copy.deepcopy(state["tasks"]), "next_id": state["next_id"]})


def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def task_line(task):
    mark = "x" if task.get("done") else " "
    line = f"{task['id']} [{mark}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def parse_date(value):
    """Return the value if it is a valid YYYY-MM-DD date, else None."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        return None
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return None
    return value


def cmd_add(args):
    if args.priority not in PRIORITIES:
        print(f"Invalid priority: {args.priority}", file=sys.stderr)
        return 1
    due = None
    if args.due is not None:
        due = parse_date(args.due)
        if due is None:
            print(f"Invalid date: {args.due}", file=sys.stderr)
            return 1
    state = load_state()
    record(state)
    task_id = state["next_id"]
    state["tasks"].append({"id": task_id, "title": args.title, "done": False,
                           "priority": args.priority, "tags": list(args.tag or []),
                           "due": due})
    state["next_id"] = task_id + 1
    save_state(state)
    print(f"Added {task_id}")
    return 0


def cmd_list(args):
    state = load_state()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]
    if args.overdue:
        today = args.today
        if today is None:
            today = datetime.date.today().isoformat()
        elif parse_date(today) is None:
            print(f"Invalid date: {today}", file=sys.stderr)
            return 1
        tasks = [t for t in tasks if not t.get("done") and t.get("due")
                 and t["due"] < today]
    if args.sort == "priority":
        tasks = sorted(tasks, key=lambda t: PRIORITY_RANK[t.get("priority", "medium")])
    if not tasks:
        print("No tasks")
        return 0
    for task in tasks:
        print(task_line(task))
    return 0


def find_task(state, task_id):
    for task in state["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def cmd_done(args):
    state = load_state()
    task = find_task(state, args.id)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        return 1
    record(state)
    task["done"] = True
    save_state(state)
    print(f"Done {args.id}")
    return 0


def cmd_delete(args):
    state = load_state()
    task = find_task(state, args.id)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        return 1
    record(state)
    state["tasks"].remove(task)
    save_state(state)
    print(f"Deleted {args.id}")
    return 0


def cmd_edit(args):
    state = load_state()
    task = find_task(state, args.id)
    if task is None:
        print(f"No such task: {args.id}", file=sys.stderr)
        return 1
    record(state)
    if args.title is not None:
        task["title"] = " ".join(args.title)
    save_state(state)
    print(f"Edited {args.id}")
    return 0


def cmd_search(args):
    state = load_state()
    needle = args.text.lower()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    tasks = [t for t in tasks if needle in t["title"].lower()]
    if not tasks:
        print("No matches")
        return 0
    for task in tasks:
        print(task_line(task))
    return 0


def cmd_export(args):
    state = load_state()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    rows = [{"id": t["id"], "title": t["title"], "done": bool(t.get("done")),
             "priority": t.get("priority", "medium"), "tags": list(t.get("tags", [])),
             "due": t.get("due") or None} for t in tasks]
    if args.format == "json":
        print(json.dumps(rows, indent=2))
        return 0
    print("id,title,done,priority,tags,due")
    for r in rows:
        print(",".join([str(r["id"]), r["title"], "true" if r["done"] else "false",
                        r["priority"], ";".join(r["tags"]), r["due"] or ""]))
    return 0


def cmd_stats(args):
    state = load_state()
    total = len(state["tasks"])
    done = sum(1 for t in state["tasks"] if t.get("done"))
    print(f"open: {total - done}")
    print(f"done: {done}")
    print(f"total: {total}")
    return 0


def cmd_undo(args):
    state = load_state()
    history = state.get("history", [])
    if not history:
        print("Nothing to undo", file=sys.stderr)
        return 1
    snap = history.pop()
    state["tasks"] = snap["tasks"]
    state["next_id"] = snap["next_id"]
    save_state(state)
    print("Undone")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="tasks.py")
    sub = parser.add_subparsers(dest="command", required=True)
    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--tag", action="append", default=[])
    p_add.add_argument("--due", default=None)
    p_add.set_defaults(func=cmd_add)
    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)
    p_delete = sub.add_parser("delete", help="delete a task")
    p_delete.add_argument("id", type=int)
    p_delete.set_defaults(func=cmd_delete)
    p_edit = sub.add_parser("edit", help="edit a task")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+", default=None)
    p_edit.set_defaults(func=cmd_edit)
    p_search = sub.add_parser("search", help="search task titles")
    p_search.add_argument("text")
    p_search.set_defaults(func=cmd_search)
    p_export = sub.add_parser("export", help="export tasks")
    p_export.add_argument("--format", choices=["json", "csv"], required=True)
    p_export.set_defaults(func=cmd_export)
    p_undo = sub.add_parser("undo", help="undo the last mutating command")
    p_undo.set_defaults(func=cmd_undo)
    p_stats = sub.add_parser("stats", help="show task counts")
    p_stats.set_defaults(func=cmd_stats)
    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--sort", choices=["id", "priority"], default="id")
    p_list.add_argument("--tag", default=None)
    p_list.add_argument("--overdue", action="store_true")
    p_list.add_argument("--today", default=None)
    p_list.set_defaults(func=cmd_list)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
