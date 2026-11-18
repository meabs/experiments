#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def task_line(task):
    """Format a task as a display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    title = task["title"]
    suffixes = []
    # priority suffix (feature 5)
    p = task.get("priority", "medium")
    if p == "high":
        suffixes.append("(high)")
    elif p == "low":
        suffixes.append("(low)")
    # tags suffix (feature 6)
    for tag in task.get("tags", []):
        suffixes.append(f"#{tag}")
    # due date suffix (feature 7)
    if task.get("due"):
        suffixes.append(f"due:{task['due']}")
    parts = [f"{tid} {status} {title}"] + suffixes
    return " ".join(parts)


def cmd_add(args):
    """Handle 'add' command."""
    data = load_data()
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
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
            title_parts.append(arg)
            i += 1

    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    tid = data["next_id"]
    task = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][str(tid)] = task
    data["next_id"] = tid + 1

    # Save undo state before mutating
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Added {tid}")


def cmd_list(args):
    """Handle 'list' command."""
    data = load_data()
    tasks = list(data["tasks"].values())

    # Parse options
    sort_by_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_by_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
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

    # Filter by tag
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    # Overdue filter (feature 7)
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    # Sort
    if sort_by_priority:
        order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args):
    """Handle 'done' command."""
    data = load_data()
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    tid = int(args[0])
    key = str(tid)
    if key not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    data["tasks"][key]["done"] = True

    # Save undo state before mutating
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args):
    """Handle 'delete' command."""
    data = load_data()
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    tid = int(args[0])
    key = str(tid)
    if key not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    del data["tasks"][key]

    # Save undo state before mutating
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args):
    """Handle 'edit' command."""
    data = load_data()
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    tid = int(args[0])
    key = str(tid)
    if key not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        else:
            i += 1

    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    data["tasks"][key]["title"] = new_title

    # Save undo state before mutating
    data["history"].append(json.dumps({"tasks": data["tasks"], "next_id": data["next_id"]}))
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args):
    """Handle 'search' command."""
    data = load_data()
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if query in t["title"].lower()]
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args):
    """Handle 'export' command."""
    data = load_data()
    if not args or args[0] != "--format":
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    fmt = args[1] if len(args) > 1 else ""
    if fmt not in ("json", "csv"):
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

    if fmt == "json":
        out = []
        for t in tasks:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(out))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args):
    """Handle 'stats' command."""
    data = load_data()
    tasks = list(data["tasks"].values())
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
    prev_state = json.loads(data["history"].pop())
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
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
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[cmd](sys.argv[2:])


if __name__ == "__main__":
    main()
