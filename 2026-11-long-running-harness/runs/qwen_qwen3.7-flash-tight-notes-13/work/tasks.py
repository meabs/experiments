#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    """Load tasks from data file."""
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    """Save tasks to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    """Load undo history from file."""
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    """Save undo history to file."""
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def error(msg):
    """Print error message to stderr and exit."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    # Priority suffix (high and low only, medium is no suffix)
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    """Handle 'add' command."""
    tasks, next_id = load_tasks()

    title_parts = []
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                error(f"Invalid priority: {val}")
            priority = val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value after --tag")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("Invalid date: ")
            val = args[i + 1]
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {val}")
            due = val
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        error("Missing task title")

    title = " ".join(title_parts)

    # Save pre-mutation state for undo
    prev_state = {"tasks": list(tasks), "next_id": next_id}

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

    # Save post-mutation state for undo
    history = load_undo_history()
    history.append(prev_state)
    save_undo_history(history)

    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    tasks, _ = load_tasks()

    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("Missing sort value")
            if args[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("Missing tag value after --tag")
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("Missing date value after --today")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue:
        if today_str is None:
            today_str = date.today().isoformat()
        try:
            datetime.strptime(today_str, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {today_str}")
        today = date.fromisoformat(today_str)
        filtered = [
            t for t in tasks
            if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today
        ]
    elif filter_tag:
        filtered = [t for t in tasks if filter_tag in t.get("tags", [])]
    else:
        filtered = list(tasks)

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for t in filtered:
        print(task_line(t))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks, next_id = load_tasks()
    found = False
    for t in tasks:
        if t["id"] == task_id:
            # Save pre-mutation state for undo
            prev_state = {"tasks": list(tasks), "next_id": next_id}
            t["done"] = True
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    save_tasks(tasks, next_id)

    # Save post-mutation state for undo
    history = load_undo_history()
    history.append(prev_state)
    save_undo_history(history)

    print(f"Done {task_id}")


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks, next_id = load_tasks()
    found = False
    new_tasks = []
    for t in tasks:
        if t["id"] == task_id:
            found = True
        else:
            new_tasks.append(t)

    if not found:
        error(f"No such task: {task_id}")

    # Save pre-mutation state for undo
    prev_state = {"tasks": list(tasks), "next_id": next_id}

    save_tasks(new_tasks, next_id)

    # Save post-mutation state for undo
    history = load_undo_history()
    history.append(prev_state)
    save_undo_history(history)

    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args:
        error("Missing task id")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid task id: {args[0]}")

    tasks, next_id = load_tasks()
    found = False
    new_title = None

    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("Missing title value after --title")
            new_title = " ".join(args[i + 1:])
            break
        else:
            i += 1

    if new_title is None:
        error("Missing --title argument")

    for t in tasks:
        if t["id"] == task_id:
            # Save pre-mutation state for undo
            prev_state = {"tasks": list(tasks), "next_id": next_id}
            t["title"] = new_title
            found = True
            break

    if not found:
        error(f"No such task: {task_id}")

    save_tasks(tasks, next_id)

    # Save post-mutation state for undo
    history = load_undo_history()
    history.append(prev_state)
    save_undo_history(history)

    print(f"Edited {task_id}")


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        error("Missing search text")

    query = " ".join(args).lower()
    tasks, _ = load_tasks()

    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                error("Missing format value")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt:
        error("Missing --format argument")

    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")

    tasks, _ = load_tasks()
    tasks.sort(key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    """Handle 'stats' command."""
    tasks, _ = load_tasks()

    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)

    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    history = load_undo_history()

    if not history:
        error("Nothing to undo")

    prev_state = history.pop()
    save_tasks(prev_state["tasks"], prev_state["next_id"])
    save_undo_history(history)

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
        error("Usage: python3 tasks.py <command> [args]")

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        error(f"Unknown command: {command}")

    COMMANDS[command](args)


if __name__ == "__main__":
    main()
