#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from JSON file. Return (tasks_dict, next_id)."""
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = {}
    for t in data.get("tasks", []):
        tid = t.get("id")
        if tid is None:
            continue
        tasks[tid] = t
    next_id = data.get("next_id", 1)
    return tasks, next_id


def save_tasks(tasks, next_id):
    """Save tasks to JSON file."""
    # Ensure every task has an 'id' field
    for tid, t in tasks.items():
        t.setdefault("id", tid)
    data = {
        "tasks": list(tasks.values()),
        "next_id": next_id,
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def parse_add_args(args):
    """Parse add arguments: extract title, --priority, --tag and --due flags."""
    valid_priorities = {"high", "medium", "low"}
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Usage: add TITLE --priority high|medium|low", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in valid_priorities:
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Usage: add TITLE --tag TAG", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Usage: add TITLE --due YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            # Validate date format YYYY-MM-DD
            try:
                parsed = datetime.strptime(due_str, "%Y-%m-%d")
                # Verify it round-trips (catches things like 2024-02-30)
                if parsed.strftime("%Y-%m-%d") != due_str:
                    print(f"Invalid date: {due_str}", file=sys.stderr)
                    sys.exit(1)
                due = due_str
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    title = " ".join(title_parts)
    return title, priority, tags, due


def task_line(task):
    """Build the display line for a task."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    title = task["title"]
    parts = [f"{tid} {status} {title}"]

    # Priority suffix (feature 5): (high) or (low), nothing for medium
    priority = task.get("priority", "medium")
    if priority == "high":
        parts.append("(high)")
    elif priority == "low":
        parts.append("(low)")

    # Tags suffix (feature 6): #tag1 #tag2
    tags = task.get("tags", [])
    for tag in tags:
        parts.append(f"#{tag}")

    # Due date suffix (feature 7): due:YYYY-MM-DD
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")

    return " ".join(parts)


def cmd_add(args):
    title, priority, tags, due = parse_add_args(args)
    tasks, next_id = load_tasks()
    task = {
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks[next_id] = task
    save_tasks(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks, _ = load_tasks()
    if not tasks:
        print("No tasks")
        return

    # Check for --sort priority
    sort_priority = "--sort" in args
    sort_index = args.index("--sort") if sort_priority else -1
    if sort_priority and sort_index + 1 < len(args) and args[sort_index + 1] == "priority":
        # Sort by priority order: high(0), medium(1), low(2), then by id
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_ids = sorted(
            tasks.keys(),
            key=lambda tid: (priority_order.get(tasks[tid].get("priority", "medium"), 1), tid)
        )
    else:
        sorted_ids = sorted(tasks.keys())

    # Check for --tag filter
    tag_filter = None
    if "--tag" in args:
        tag_index = args.index("--tag")
        if tag_index + 1 < len(args):
            tag_filter = args[tag_index + 1]

    # Check for --overdue filter
    overdue = False
    today_str = None
    if "--overdue" in args:
        overdue = True
        # Find --today value
        if "--today" in args:
            today_idx = args.index("--today")
            if today_idx + 1 < len(args):
                today_str = args[today_idx + 1]

    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()

    for tid in sorted_ids:
        task = tasks[tid]
        # Apply tag filter if present
        if tag_filter is not None:
            task_tags = task.get("tags", [])
            if tag_filter not in task_tags:
                continue

        # Apply overdue filter: only open tasks due before today
        if overdue:
            task_due = task.get("due")
            if not task_due or task["done"]:
                continue
            try:
                task_date = datetime.strptime(task_due, "%Y-%m-%d").date()
            except ValueError:
                continue
            if task_date >= today:
                continue

        print(task_line(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")



def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    # Parse --title flag
    title_index = None
    for i, arg in enumerate(args):
        if arg == "--title":
            title_index = i + 1
            break
    if title_index is None or title_index >= len(args):
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(args[title_index:])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")



COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[cmd](args)


if __name__ == "__main__":
    main()
