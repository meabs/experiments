#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
import argparse
import copy
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    """Load tasks from tasks.json, returning (tasks_dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = {int(k): v for k, v in data.get("tasks", {}).items()}
        next_id = data.get("next_id", 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return {}, 1


def save_tasks(tasks, next_id):
    """Save tasks to tasks.json."""
    data = {"tasks": {str(k): v for k, v in tasks.items()}, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    """Load undo history from undo_history.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []


def save_undo_history(history):
    """Save undo history to undo_history.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def record_undo(tasks, next_id):
    """Record current state for undo."""
    history = load_undo_history()
    snapshot = {"tasks": {str(k): v for k, v in tasks.items()}, "next_id": next_id}
    history.append(snapshot)
    save_undo_history(history)


def undo_last():
    """Undo the last mutating command."""
    history = load_undo_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    snapshot = history.pop()
    save_undo_history(history)
    tasks = {int(k): v for k, v in snapshot["tasks"].items()}
    next_id = snapshot["next_id"]
    save_tasks(tasks, next_id)


def validate_date(date_str):
    """Validate a YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def task_line(task):
    """Format a task into its display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    title = task["title"]
    suffixes = []
    # priority suffix
    priority = task.get("priority", "medium")
    if priority == "high":
        suffixes.append("(high)")
    elif priority == "low":
        suffixes.append("(low)")
    # medium has no suffix
    # tags suffix
    tags = task.get("tags", [])
    for tag in tags:
        suffixes.append("#" + tag)
    # due date suffix
    due = task.get("due", None)
    if due:
        suffixes.append("due:" + due)
    line = "{} {} {}".format(tid, status, title)
    if suffixes:
        line += " " + " ".join(suffixes)
    return line


def parse_add_args(args):
    """Parse arguments for add command."""
    parser = argparse.ArgumentParser(prog="add")
    parser.add_argument("title", nargs="+")
    parser.add_argument("--priority", default="medium")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--due", default=None)
    parsed = parser.parse_args(args)
    title = " ".join(parsed.title)
    priority = parsed.priority
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)
    due = parsed.due
    if due is not None:
        if not validate_date(due):
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)
    return title, priority, parsed.tag, due


def cmd_add(args):
    """Handle the add command."""
    title, priority, tags, due = parse_add_args(args)
    tasks, next_id = load_tasks()
    record_undo(tasks, next_id)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks[next_id] = task
    save_tasks(tasks, next_id + 1)
    print("Added {}".format(next_id))


def cmd_list(args):
    """Handle the list command."""
    parser = argparse.ArgumentParser(prog="list")
    parser.add_argument("--sort", default=None)
    parser.add_argument("--tag", default=None)
    parser.add_argument("--overdue", action="store_true")
    parser.add_argument("--today", default=None)
    parsed = parser.parse_args(args)

    tasks, _ = load_tasks()

    # Filter by tag
    if parsed.tag:
        tasks = {k: v for k, v in tasks.items() if parsed.tag in v.get("tags", [])}

    # Overdue filter: only open tasks with due date before today
    if parsed.overdue:
        today_str = parsed.today or date.today().isoformat()
        if not validate_date(today_str):
            print("Invalid date: {}".format(today_str), file=sys.stderr)
            sys.exit(1)
        today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        filtered = {}
        for k, v in tasks.items():
            if v.get("done"):
                continue
            due = v.get("due")
            if due is None:
                continue
            try:
                due_date = datetime.strptime(due, "%Y-%m-%d").date()
                if due_date < today_date:
                    filtered[k] = v
            except ValueError:
                continue
        tasks = filtered

    if not tasks:
        print("No tasks")
        return

    # Sort
    if parsed.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_ids = sorted(
            tasks.keys(), key=lambda k: (priority_order.get(tasks[k].get("priority", "medium"), 1), k)
        )
    else:
        sorted_ids = sorted(tasks.keys())

    for tid in sorted_ids:
        print(task_line(tasks[tid]))


def cmd_done(args):
    """Handle the done command."""
    parser = argparse.ArgumentParser(prog="done")
    parser.add_argument("task_id", type=int)
    parsed = parser.parse_args(args)
    tid = parsed.task_id
    tasks, next_id = load_tasks()
    if tid not in tasks:
        print("No such task: {}".format(tid), file=sys.stderr)
        sys.exit(1)
    record_undo(tasks, next_id)
    tasks[tid]["done"] = True
    save_tasks(tasks, next_id)
    print("Done {}".format(tid))


def cmd_delete(args):
    """Handle the delete command."""
    parser = argparse.ArgumentParser(prog="delete")
    parser.add_argument("task_id", type=int)
    parsed = parser.parse_args(args)
    tid = parsed.task_id
    tasks, next_id = load_tasks()
    if tid not in tasks:
        print("No such task: {}".format(tid), file=sys.stderr)
        sys.exit(1)
    record_undo(tasks, next_id)
    del tasks[tid]
    save_tasks(tasks, next_id)
    print("Deleted {}".format(tid))


def cmd_edit(args):
    """Handle the edit command."""
    parser = argparse.ArgumentParser(prog="edit")
    parser.add_argument("task_id", type=int)
    parser.add_argument("--title", nargs="+", required=True)
    parsed = parser.parse_args(args)
    tid = parsed.task_id
    new_title = " ".join(parsed.title)
    tasks, next_id = load_tasks()
    if tid not in tasks:
        print("No such task: {}".format(tid), file=sys.stderr)
        sys.exit(1)
    record_undo(tasks, next_id)
    tasks[tid]["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited {}".format(tid))


def cmd_search(args):
    """Handle the search command."""
    if not args:
        print("No matches")
        return
    text = " ".join(args).lower()
    tasks, _ = load_tasks()
    matched = {k: v for k, v in tasks.items() if text in v["title"].lower()}
    if not matched:
        print("No matches")
        return
    for tid in sorted(matched.keys()):
        print(task_line(matched[tid]))


def cmd_export(args):
    """Handle the export command."""
    parser = argparse.ArgumentParser(prog="export")
    parser.add_argument("--format", choices=["json", "csv"], required=True)
    parsed = parser.parse_args(args)
    tasks, _ = load_tasks()
    if parsed.format == "json":
        result = []
        for tid in sorted(tasks.keys()):
            t = tasks[tid]
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(result))
    elif parsed.format == "csv":
        print("id,title,done,priority,tags,due")
        for tid in sorted(tasks.keys()):
            t = tasks[tid]
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str
            ))


def cmd_stats(args):
    """Handle the stats command."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    """Handle the undo command."""
    undo_last()
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
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    args = sys.argv[2:]
    COMMANDS[command](args)


if __name__ == "__main__":
    main()
