#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import copy
import csv
import io
import json
import os
import sys
from datetime import date, datetime


TASKS_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_tasks():
    """Load tasks from tasks.json."""
    if not os.path.exists(TASKS_FILE):
        return [], 1
    try:
        with open(TASKS_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        next_id = data.get("next_id", 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    """Save tasks to tasks.json."""
    with open(TASKS_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    """Load undo history from history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    """Save undo history to history.json."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def format_task(task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    if task.get("tags"):
        tags_str = " ".join(f"#{t}" for t in task["tags"])
        line += " " + tags_str
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def add_task(args):
    """Handle 'add' command."""
    title = " ".join(args.title)
    priority = getattr(args, "priority", "medium") or "medium"
    tags = getattr(args, "tag", None) or []
    due = getattr(args, "due", None)

    if priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")

    if due:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    tasks, next_id = load_tasks()

    # Save pre-mutation state for undo
    history = load_history()
    history.append({
        "action": "add",
        "state": {"tasks": copy.deepcopy(tasks), "next_id": next_id},
    })
    save_history(history)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    next_id += 1

    save_tasks(tasks, next_id)
    print(f"Added {task['id']}")


def list_tasks(args):
    """Handle 'list' command."""
    tasks, _ = load_tasks()

    # Filter by tag
    tag_filter = getattr(args, "tag", None)
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    # Filter overdue
    overdue = getattr(args, "overdue", None)
    if overdue:
        today_str = getattr(args, "today", None) or date.today().isoformat()
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    # Sort by priority
    sort_by_priority = getattr(args, "sort", None)
    if sort_by_priority == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    if not tasks:
        print("No tasks")
        return

    # Sort by id unless we're sorting by priority
    if sort_by_priority != "priority":
        tasks.sort(key=lambda t: t["id"])

    for task in tasks:
        print(format_task(task))


def done_task(args):
    """Handle 'done' command."""
    task_id = args.id
    tasks, next_id = load_tasks()

    # Save pre-mutation state for undo
    history = load_history()
    history.append({
        "action": "done",
        "state": {"tasks": copy.deepcopy(tasks), "next_id": next_id},
    })
    save_history(history)

    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if not found:
        error(f"No such task: {task_id}")
    found["done"] = True

    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def delete_task(args):
    """Handle 'delete' command."""
    task_id = args.id
    tasks, next_id = load_tasks()

    # Save pre-mutation state for undo
    history = load_history()
    history.append({
        "action": "delete",
        "state": {"tasks": copy.deepcopy(tasks), "next_id": next_id},
    })
    save_history(history)

    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if not found:
        error(f"No such task: {task_id}")
    tasks = [t for t in tasks if t["id"] != task_id]

    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def edit_task(args):
    """Handle 'edit' command."""
    task_id = args.id
    new_title = " ".join(args.title)
    tasks, next_id = load_tasks()

    # Save pre-mutation state for undo
    history = load_history()
    history.append({
        "action": "edit",
        "state": {"tasks": copy.deepcopy(tasks), "next_id": next_id},
    })
    save_history(history)

    found = None
    for t in tasks:
        if t["id"] == task_id:
            found = t
            break
    if not found:
        error(f"No such task: {task_id}")
    found["title"] = new_title

    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def search_tasks(args):
    """Handle 'search' command."""
    tasks, _ = load_tasks()
    text = args.text.lower()
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in sorted(matches, key=lambda t: t["id"]):
        print(format_task(task))


def export_tasks(args):
    """Handle 'export' command."""
    tasks, _ = load_tasks()
    fmt = getattr(args, "format", "json") or "json"
    tasks = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(result))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_val = t.get("due", "")
            writer.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t.get("priority", "medium"),
                tags_str,
                due_val,
            ])
        print(output.getvalue(), end="")


def stats_task(args):
    """Handle 'stats' command."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def undo_command(args):
    """Handle 'undo' command."""
    history = load_history()
    if not history:
        error("Nothing to undo")
    last = history.pop()
    save_history(history)
    state = last["state"]
    save_tasks(state["tasks"], state["next_id"])
    print("Undone")


def main():
    parser = argparse.ArgumentParser(prog="tasks.py", description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=None)
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", default=None)
    list_parser.add_argument("--tag", default=None)
    list_parser.add_argument("--overdue", action="store_true")
    list_parser.add_argument("--today", default=None)

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    # delete
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)

    # edit
    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("--title", nargs="+", required=True)

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", default="json")

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    commands = {
        "add": add_task,
        "list": list_tasks,
        "done": done_task,
        "delete": delete_task,
        "edit": edit_task,
        "search": search_tasks,
        "export": export_tasks,
        "stats": stats_task,
        "undo": undo_command,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
