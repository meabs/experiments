#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and state from data file."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and state to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def task_line(task):
    """Format a task as a display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"
    # Priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # medium has no suffix
    # Tags suffix
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # Due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def record_history(data, snapshot):
    """Record a snapshot of data before mutation for undo."""
    data["history"].append(json.loads(json.dumps(snapshot)))


def cmd_add(args, data):
    """Handle 'add' command."""
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
                i += 2
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    next_id = data["next_id"]
    data["tasks"][next_id] = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["next_id"] = next_id + 1
    print(f"Added {next_id}")


def cmd_list(args, data):
    """Handle 'list' command."""
    tasks = list(data["tasks"].values())
    
    # Filter by tag
    tag_filter = None
    sort_by = None
    overdue = False
    today_str = None
    
    i = 0
    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a value", file=sys.stderr)
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

    # Apply filters
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    
    if overdue:
        today = today_str or date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    # Sort
    if sort_by == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for t in tasks:
            print(task_line(t))


def cmd_done(args, data):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    data["tasks"][tid]["done"] = True
    print(f"Done {tid}")


def cmd_delete(args, data):
    """Handle 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    if tid not in data["tasks"]:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)
    del data["tasks"][tid]
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    """Handle 'edit' command."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)
    if tid not in data["tasks"]:
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
        else:
            i += 1

    if new_title is None:
        print("--title is required", file=sys.stderr)
        sys.exit(1)

    data["tasks"][tid]["title"] = new_title
    print(f"Edited {tid}")


def cmd_search(args, data):
    """Handle 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    results = []
    for t in sorted(data["tasks"].values(), key=lambda x: x["id"]):
        if text in t["title"].lower():
            results.append(t)
    if not results:
        print("No matches")
    else:
        for t in results:
            print(task_line(t))


def cmd_export(args, data):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires a value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])

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
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority', 'medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    """Handle 'stats' command."""
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args, data):
    """Handle 'undo' command."""
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]
    data = load_data()

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

    if command not in commands:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    # For mutating commands, snapshot before execution
    mutating = {"add", "done", "delete", "edit"}
    if command in mutating:
        record_history(data, json.loads(json.dumps(data)))

    commands[command](args, data)
    save_data(data)


if __name__ == "__main__":
    main()
