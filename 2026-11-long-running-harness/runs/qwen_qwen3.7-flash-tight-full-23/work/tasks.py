#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys


DATA_FILE = "tasks.json"
UNDO_FILE = ".undo.json"


def load_tasks():
    """Load tasks from tasks.json."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    """Save tasks to tasks.json."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    """Load undo history from .undo.json."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    """Save undo history to .undo.json."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo_state(tasks, next_id):
    """Push current state onto the undo stack."""
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_undo_history(history)


def format_task(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {status} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle 'add' command."""
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due" and i + 1 < len(args):
            due = args[i + 1]
            try:
                import calendar
                parts = due.split("-")
                if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                    raise ValueError
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if month < 1 or month > 12 or day < 1 or day > 31:
                    raise ValueError
                max_day = calendar.monthrange(year, month)[1]
                if day > max_day:
                    raise ValueError
            except (ValueError, IndexError):
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif title is None:
            title = args[i]
            i += 1
        else:
            i += 1

    if title is None:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    push_undo_state(tasks, next_id)

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


def cmd_list(args):
    """Handle 'list' command."""
    sort_mode = None
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    tasks, _ = load_tasks()

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if overdue:
        import datetime
        if today_str:
            today = datetime.date.fromisoformat(today_str)
        else:
            today = datetime.date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < str(today)]

    if not tasks:
        print("No tasks")
        return

    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))

    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    push_undo_state(tasks, next_id)
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    push_undo_state(tasks, next_id)
    new_tasks = []
    for task in tasks:
        if task["id"] == task_id:
            found = True
        else:
            new_tasks.append(task)
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(new_tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    task_id = None
    new_title = None
    i = 0
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            j = i + 1
            while j < len(args) and not args[j].startswith("--"):
                j += 1
            new_title = " ".join(args[i + 1:j])
            i = j
        else:
            if task_id is None:
                task_id = args[i]
            i += 1

    if task_id is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    try:
        task_id = int(task_id)
    except ValueError:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    found = False
    push_undo_state(tasks, next_id)
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break
    if not found:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()

    tasks, _ = load_tasks()
    matches = [t for t in tasks if text in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task(task))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()

    if fmt == "json":
        export_data = []
        for task in tasks:
            export_data.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due", None),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due", "") or ""
            print(f"{task['id']},{task['title']},{str(task['done']).lower()},{task.get('priority','medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Handle 'stats' command."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = args[0]
    rest = args[1:]

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
        "delete": cmd_delete,
        "edit": cmd_edit,
        "search": cmd_search,
        "export": cmd_export,
        "stats": cmd_stats,
        "undo": lambda _: undo(),
    }

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    commands[command](rest)


if __name__ == "__main__":
    main()
