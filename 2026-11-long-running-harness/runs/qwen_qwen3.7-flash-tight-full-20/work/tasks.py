#!/usr/bin/env python3
"""A command-line task manager."""

import sys
import os
import json
import argparse
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from JSON file, creating if needed."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def format_task(task):
    """Format a task for display in list/search."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"

    # Priority suffix (only non-medium)
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"

    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{tag}" for tag in tags)

    # Due date suffix
    due = task.get("due")
    if due:
        line += f" due:{due}"

    return line


def push_history(data):
    """Push current state onto undo history."""
    data["history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })


def cmd_add(args):
    """Handle 'add' command."""
    data = load_data()

    priority = args.priority
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)

    tags = getattr(args, "tag", []) or []
    due = getattr(args, "due", None)

    # Validate due date
    if due:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)

    title = " ".join(args.title)

    # Save state for undo
    push_history(data)

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    data["tasks"].append(task)
    data["next_id"] += 1

    save_data(data)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = data["tasks"]

    # Filter by tag if specified
    if hasattr(args, "tag") and args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]

    # Filter overdue if specified
    if hasattr(args, "overdue") and args.overdue:
        today_str = getattr(args, "today", None)
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()

        filtered = []
        for t in tasks:
            if t.get("due") and not t["done"]:
                try:
                    due_date = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if due_date < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    if not tasks:
        print("No tasks")
        return

    # Sort by priority if requested
    if hasattr(args, "sort") and args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Handle 'done' command."""
    data = load_data()
    tid = args.id

    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    push_history(data)

    task["done"] = True
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args):
    """Handle 'delete' command."""
    data = load_data()
    tid = args.id

    task = None
    for i, t in enumerate(data["tasks"]):
        if t["id"] == tid:
            task = t
            break

    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    push_history(data)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args):
    """Handle 'edit' command."""
    data = load_data()
    tid = args.id

    task = None
    for t in data["tasks"]:
        if t["id"] == tid:
            task = t
            break

    if task is None:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Save state for undo
    push_history(data)

    new_title = " ".join(args.title)
    task["title"] = new_title

    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args):
    """Handle 'search' command."""
    data = load_data()
    text = " ".join(args.text).lower()

    matches = []
    for t in data["tasks"]:
        if text in t["title"].lower():
            matches.append(t)

    if not matches:
        print("No matches")
        return

    for t in sorted(matches, key=lambda x: x["id"]):
        print(format_task(t))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(result, indent=2))

    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            lines.append(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
        print("\n".join(lines))


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    data = load_data()

    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    save_data(data)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("title", nargs="+")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=[])
    add_parser.add_argument("--due", default=None)

    # list
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--sort", choices=["priority"])
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
    edit_parser.add_argument("--title", nargs="+")

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("text", nargs="+")

    # export
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--format", choices=["json", "csv"], required=True)

    # stats
    subparsers.add_parser("stats")

    # undo
    subparsers.add_parser("undo")

    args = parser.parse_args()

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

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
