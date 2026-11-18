#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys

DATA_FILE = "tasks.json"


def load_tasks():
    """Load tasks from JSON file, creating it if needed."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    return [], 1


def save_tasks(tasks, next_id):
    """Save tasks to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def format_task(task):
    """Format a task as a display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [f'{task["id"]} {status} {task["title"]}']
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # Tags suffix
    tags = task.get("tags", [])
    if tags:
        parts.append(" ".join(f"#{t}" for t in tags))
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args):
    """Handle 'add' command."""
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Error: --priority requires a value", file=sys.stderr)
                sys.exit(1)
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                print(f"Invalid priority: {val}", file=sys.stderr)
                sys.exit(1)
            priority = val
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Error: --due requires a value", file=sys.stderr)
                sys.exit(1)
            val = args[i + 1]
            import datetime
            try:
                datetime.datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {val}", file=sys.stderr)
                sys.exit(1)
            due = val
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    
    if not title_parts:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)
    
    title = " ".join(title_parts)
    
    tasks, next_id = load_tasks()
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print(f"Added {task['id']}")


def cmd_list(args):
    """Handle 'list' command."""
    tasks, _ = load_tasks()
    
    sort_mode = None
    tag_filter = None
    show_overdue = False
    today_str = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            i += 1
            if i < len(args):
                sort_mode = args[i]
        elif arg == "--tag":
            i += 1
            if i < len(args):
                tag_filter = args[i]
        elif arg == "--overdue":
            show_overdue = True
        elif arg == "--today":
            i += 1
            if i < len(args):
                today_str = args[i]
        i += 1
    
    # Filter by tag if specified
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    
    # Filter overdue
    if show_overdue:
        import datetime
        if today_str:
            today = datetime.date.fromisoformat(today_str)
        else:
            today = datetime.date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due")
            and datetime.date.fromisoformat(t["due"]) < today
        ]
    
    # Sort
    if sort_mode == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    
    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(format_task(task))


def cmd_done(args):
    """Handle 'done' command."""
    if not args or not args[0].isdigit():
        print("Error: done requires an ID", file=sys.stderr)
        sys.exit(1)
    
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks, next_id)
            print(f"Done {task_id}")
            return
    
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args or not args[0].isdigit():
        print("Error: delete requires an ID", file=sys.stderr)
        sys.exit(1)
    
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    
    save_tasks(new_tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    """Handle 'edit' command."""
    if not args or not args[0].isdigit():
        print("Error: edit requires an ID", file=sys.stderr)
        sys.exit(1)
    
    task_id = int(args[0])
    tasks, next_id = load_tasks()
    
    title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            if i < len(args):
                title = args[i] + (" " + " ".join(args[i+1:]) if args[i+1:] else "")
            break
        i += 1
    
    if title is None:
        print("Error: edit --title requires a new title", file=sys.stderr)
        sys.exit(1)
    
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = title
            save_tasks(tasks, next_id)
            print(f"Edited {task_id}")
            return
    
    print(f"No such task: {task_id}", file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        print("Error: search requires text", file=sys.stderr)
        sys.exit(1)
    
    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    
    matches = [t for t in tasks if query in t["title"].lower()]
    
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task(task))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    for i, arg in enumerate(args):
        if arg == "--format":
            i += 1
            if i < len(args):
                fmt = args[i]
    
    if fmt not in ("json", "csv"):
        print("Error: export requires --format json or csv", file=sys.stderr)
        sys.exit(1)
    
    tasks, _ = load_tasks()
    
    if fmt == "json":
        export_data = []
        for t in sorted(tasks, key=lambda x: x["id"]):
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
        for t in sorted(tasks, key=lambda x: x["id"]):
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{done_str},{t.get("priority","medium")},{tags_str},{due_str}')


def cmd_stats(args):
    """Handle 'stats' command."""
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args):
    """Handle 'undo' command."""
    undo_file = "tasks.json.undo"
    
    if not os.path.exists(undo_file):
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    
    with open(undo_file, "r") as f:
        state = json.load(f)
    
    save_tasks(state["tasks"], state["next_id"])
    os.remove(undo_file)
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
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
