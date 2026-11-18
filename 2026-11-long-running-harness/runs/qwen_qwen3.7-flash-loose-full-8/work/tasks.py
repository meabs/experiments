#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
import argparse
import copy


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and state from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and state to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def record_undo(data, snapshot):
    """Record a snapshot for undo."""
    data["history"].append(copy.deepcopy(snapshot))


def task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    suffixes = []
    # priority suffix
    if task.get("priority") == "high":
        suffixes.append("(high)")
    elif task.get("priority") == "low":
        suffixes.append("(low)")
    # medium has no suffix
    # tags suffix
    if task.get("tags"):
        suffixes.append(" ".join("#" + t for t in task["tags"]))
    # due date suffix
    if task.get("due"):
        suffixes.append("due:" + task["due"])
    return "{} {} {}".format(task["id"], status, task["title"]) + (
        (" " + " ".join(suffixes)) if suffixes else ""
    )


# --- Commands ---

def cmd_add(args):
    """Add a new task."""
    data = load_data()
    
    # Validate priority if given
    priority = getattr(args, "priority", None) or "medium"
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)
    
    # Collect tags
    tags = list(getattr(args, "tag", []) or [])
    
    # Collect due date
    due = getattr(args, "due", None)
    
    # Validate date format if given
    if due:
        try:
            parts = due.split("-")
            if len(parts) != 3:
                raise ValueError
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            if m < 1 or m > 12 or d < 1 or d > 31:
                raise ValueError
            # Basic validation - check days in month
            days_in_month = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if d > days_in_month[m]:
                raise ValueError
        except (ValueError, IndexError):
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)
    
    title = " ".join(args.title)
    
    # Snapshot before mutation
    snapshot = copy.deepcopy(data)
    
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
    
    record_undo(data, snapshot)
    save_data(data)
    
    print("Added {}".format(task["id"]))


def cmd_list(args):
    """List all tasks."""
    data = load_data()
    tasks = data["tasks"]
    
    if not tasks:
        print("No tasks")
        return
    
    # Filter by tag if specified
    if hasattr(args, "tag") and args.tag:
        filter_tag = args.tag
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    
    # Sort by priority if requested
    if hasattr(args, "sort") and args.sort == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    
    # Show overdue tasks
    if hasattr(args, "overdue") and args.overdue:
        today = getattr(args, "today", None)
        if today is None:
            import datetime
            today = datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    
    if not tasks:
        print("No tasks")
        return
    
    for task in tasks:
        print(task_line(task))


def cmd_done(args):
    """Mark a task as done."""
    data = load_data()
    task_id = args.id
    
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    
    snapshot = copy.deepcopy(data)
    task["done"] = True
    
    record_undo(data, snapshot)
    save_data(data)
    
    print("Done {}".format(task_id))


def cmd_delete(args):
    """Delete a task."""
    data = load_data()
    task_id = args.id
    
    task = None
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            task = t
            break
    
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    
    snapshot = copy.deepcopy(data)
    data["tasks"].remove(task)
    
    record_undo(data, snapshot)
    save_data(data)
    
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    """Edit a task's title."""
    data = load_data()
    task_id = args.id
    
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    
    if task is None:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    
    snapshot = copy.deepcopy(data)
    task["title"] = " ".join(args.new_title)
    
    record_undo(data, snapshot)
    save_data(data)
    
    print("Edited {}".format(task_id))


def cmd_search(args):
    """Search tasks by text in title."""
    data = load_data()
    text = args.text.lower()
    
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    
    if not matches:
        print("No matches")
        return
    
    for task in matches:
        print(task_line(task))


def cmd_export(args):
    """Export tasks in JSON or CSV format."""
    data = load_data()
    fmt = args.format
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    
    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            done_str = "true" if t["done"] else "false"
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str
            ))


def cmd_stats(args):
    """Show stats about tasks."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


def cmd_undo(args):
    """Undo the last mutating command."""
    data = load_data()
    
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    
    prev_state = data["history"].pop()
    save_data(prev_state)
    print("Undone")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("title", nargs="+")
    p_add.add_argument("--priority")
    p_add.add_argument("--tag", action="append", default=[])
    p_add.add_argument("--due", default=None)
    
    # list
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", choices=["priority"])
    p_list.add_argument("--tag", action="append", default=[])
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
    p_edit.add_argument("--title", nargs="+", required=True)
    
    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("text", nargs="+")
    
    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("--format", choices=["json", "csv"], required=True)
    
    # stats
    subparsers.add_parser("stats")
    
    # undo
    subparsers.add_parser("undo")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
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
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
