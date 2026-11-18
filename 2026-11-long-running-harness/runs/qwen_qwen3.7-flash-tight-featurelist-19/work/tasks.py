#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and next_id from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and next_id to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def get_task_line(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    suffixes = []
    # Priority suffix (only high/low)
    if task.get("priority") == "high":
        suffixes.append("(high)")
    elif task.get("priority") == "low":
        suffixes.append("(low)")
    # Tags suffix
    if task.get("tags"):
        tag_str = " ".join("#" + t for t in task["tags"])
        suffixes.append(tag_str)
    # Due date suffix
    if task.get("due"):
        suffixes.append("due:" + task["due"])
    if suffixes:
        return f'{task["id"]} {status} {task["title"]} {" ".join(suffixes)}'
    return f'{task["id"]} {status} {task["title"]}'


def cmd_add(args):
    """Handle 'add TITLE [--priority P] [--tag T] [--tag T2] [--due DATE]'."""
    data = load_data()

    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Error: --priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Error: --due requires a value", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due_str}", file=sys.stderr)
                sys.exit(1)
            due = due_str
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    if not title:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)

    task_id = data["next_id"]
    data["tasks"].append({
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    })
    data["next_id"] = task_id + 1

    # Save undo state
    data["history"].append({
        "type": "add",
        "task_id": task_id,
        "prev_next_id": task_id,
    })
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    """Handle 'list [--sort SORT] [--tag TAG] [--overdue] [--today DATE]'."""
    data = load_data()
    tasks = list(data["tasks"])

    sort_mode = None
    filter_tag = None
    overdue_only = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            filter_tag = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue_only = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Filter overdue
    if overdue_only:
        if today_str:
            today_val = today_str
        else:
            today_val = date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_val]

    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(get_task_line(task))


def cmd_done(args):
    """Handle 'done ID'."""
    data = load_data()
    task_id = int(args[0])

    for task in data["tasks"]:
        if task["id"] == task_id:
            if not task["done"]:
                data["history"].append({
                    "type": "done",
                    "task_id": task_id,
                    "prev_done": False,
                })
            task["done"] = True
            save_data(data)
            print(f"Done {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Handle 'delete ID'."""
    data = load_data()
    task_id = int(args[0])

    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["history"].append({
                "type": "delete",
                "task_id": task_id,
                "task": data["tasks"][i],
            })
            del data["tasks"][i]
            save_data(data)
            print(f"Deleted {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    """Handle 'edit ID --title NEW TITLE'."""
    data = load_data()
    task_id = int(args[0])

    title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts.append(args[i + 1])
            i += 2
        else:
            i += 1

    new_title = " ".join(title_parts)
    if not new_title:
        print("Error: edit requires a title", file=sys.stderr)
        sys.exit(1)

    for task in data["tasks"]:
        if task["id"] == task_id:
            data["history"].append({
                "type": "edit",
                "task_id": task_id,
                "prev_title": task["title"],
            })
            task["title"] = new_title
            save_data(data)
            print(f"Edited {task_id}")
            return

    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Handle 'search TEXT'."""
    data = load_data()
    query = " ".join(args).lower()
    results = [t for t in data["tasks"] if query in t["title"].lower()]
    results.sort(key=lambda t: t["id"])

    if not results:
        print("No matches")
        return

    for task in results:
        print(get_task_line(task))


def cmd_export(args):
    """Handle 'export --format json|csv'."""
    data = load_data()
    fmt = None

    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Error: --format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None:
        print("Error: export requires --format", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        result = []
        for t in tasks:
            result.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(result))
    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            tags_str = ";".join(t["tags"])
            lines.append(f'{t["id"]},{t["title"]},{str(t["done"]).lower()},{t["priority"]},{tags_str},{t["due"] or ""}')
        print("\n".join(lines))
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats():
    """Handle 'stats'."""
    data = load_data()
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo():
    """Handle 'undo'."""
    data = load_data()

    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    entry = data["history"].pop()

    if entry["type"] == "add":
        # Remove the task we just added
        data["tasks"] = [t for t in data["tasks"] if t["id"] != entry["task_id"]]
        data["next_id"] = entry["prev_next_id"]
    elif entry["type"] == "done":
        # Restore done state
        for task in data["tasks"]:
            if task["id"] == entry["task_id"]:
                task["done"] = entry["prev_done"]
                break
    elif entry["type"] == "delete":
        # Restore deleted task
        data["tasks"].append(entry["task"])
        data["tasks"].sort(key=lambda t: t["id"])
    elif entry["type"] == "edit":
        # Restore previous title
        for task in data["tasks"]:
            if task["id"] == entry["task_id"]:
                task["title"] = entry["prev_title"]
                break

    save_data(data)
    print("Undone")


if __name__ == "__main__":
    main()
