#!/usr/bin/env python3
"""Command-line task manager."""

import argparse
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def _load():
    """Load tasks and undo history from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save(data):
    """Save tasks and undo history to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def _task_line(task):
    """Format a single task line for display."""
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


def _validate_date(date_str):
    """Validate a YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cmd_add(args):
    """Handle 'add' command."""
    data = _load()
    priority = getattr(args, "priority", None) or "medium"
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        return 1

    tags = list(getattr(args, "tag", []) or [])
    due = getattr(args, "due", None)
    if due is not None:
        if not _validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            return 1

    title_text = " ".join(args.title)
    task = {
        "id": data["next_id"],
        "title": title_text,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1

    # Save undo state before mutating
    data["undo_stack"].append({
        "action": "add",
        "task_id": task["id"],
        "next_id": task["id"] + 1,
    })
    _save(data)
    print(f"Added {task['id']}")
    return 0


def cmd_list(args):
    """Handle 'list' command."""
    data = _load()
    tasks = data["tasks"]

    if not tasks:
        print("No tasks")
        return 0

    # Filter by tag
    if getattr(args, "tag", None):
        filter_tag = args.tag
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if getattr(args, "overdue", None):
        today_str = getattr(args, "today", None) or date.today().isoformat()
        today = datetime.strptime(today_str, "%Y-%m-%d").date()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today_str
        ]

    # Sort by priority
    if getattr(args, "sort", None) == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(
            tasks,
            key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]),
        )

    lines = [_task_line(t) for t in tasks]
    for line in lines:
        print(line)
    return 0


def cmd_done(args):
    """Handle 'done' command."""
    data = _load()
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1

    # Save undo state
    data["undo_stack"].append({
        "action": "done",
        "task_id": task_id,
        "prev_done": task["done"],
    })

    task["done"] = True
    _save(data)
    print(f"Done {task_id}")
    return 0


def cmd_delete(args):
    """Handle 'delete' command."""
    data = _load()
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1

    # Save undo state
    data["undo_stack"].append({
        "action": "delete",
        "task": dict(task),
    })

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    _save(data)
    print(f"Deleted {task_id}")
    return 0


def cmd_edit(args):
    """Handle 'edit' command."""
    data = _load()
    task_id = args.id
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return 1

    new_title = " ".join(args.title)
    # Save undo state
    data["undo_stack"].append({
        "action": "edit",
        "task_id": task_id,
        "prev_title": task["title"],
    })

    task["title"] = new_title
    _save(data)
    print(f"Edited {task_id}")
    return 0


def cmd_search(args):
    """Handle 'search' command."""
    data = _load()
    query = " ".join(args.text).lower()
    matches = [t for t in data["tasks"] if query in t["title"].lower()]
    if not matches:
        print("No matches")
        return 0
    lines = [_task_line(t) for t in matches]
    for line in lines:
        print(line)
    return 0


def cmd_export(args):
    """Handle 'export' command."""
    data = _load()
    fmt = args.format

    if fmt == "json":
        export_data = []
        for t in sorted(data["tasks"], key=lambda x: x["id"]):
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in sorted(data["tasks"], key=lambda x: x["id"]):
            writer.writerow([
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t.get("priority", "medium"),
                ";".join(t.get("tags", [])),
                t.get("due", ""),
            ])
        print(output.getvalue().rstrip("\n"))
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        return 1
    return 0


def cmd_stats(args):
    """Handle 'stats' command."""
    data = _load()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")
    return 0


def cmd_undo(args):
    """Handle 'undo' command."""
    data = _load()
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        return 1

    action = data["undo_stack"].pop()

    if action["action"] == "add":
        # Remove the task we added
        data["tasks"] = [t for t in data["tasks"] if t["id"] != action["task_id"]]
        data["next_id"] = action["next_id"]
    elif action["action"] == "done":
        # Restore done state
        task = next((t for t in data["tasks"] if t["id"] == action["task_id"]), None)
        if task:
            task["done"] = action["prev_done"]
    elif action["action"] == "delete":
        # Re-add the deleted task
        data["tasks"].append(action["task"])
        data["tasks"].sort(key=lambda t: t["id"])
    elif action["action"] == "edit":
        # Restore previous title
        task = next((t for t in data["tasks"] if t["id"] == action["task_id"]), None)
        if task:
            task["title"] = action["prev_title"]

    _save(data)
    print("Undone")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--tag", action="append", default=[])
    p_add.add_argument("--due", default=None)

    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", choices=["priority"])
    p_list.add_argument("--tag", default=None)
    p_list.add_argument("--overdue", action="store_true")
    p_list.add_argument("--today", default=None)

    # done
    p_done = subparsers.add_parser("done")
    p_done.add_argument("id", type=int)

    # delete
    p_delete = subparsers.add_parser("delete")
    p_delete.add_argument("id", type=int)

    # edit
    p_edit = subparsers.add_parser("edit")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title", nargs="+")

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("text", nargs="+")

    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("--format", required=True)

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    commands = {
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

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
