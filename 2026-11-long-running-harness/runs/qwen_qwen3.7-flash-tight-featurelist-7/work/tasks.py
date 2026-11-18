#!/usr/bin/env python3
import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def get_next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_history(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = history.pop()
    save_history(history)
    return state["tasks"], state["next_id"]


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    # Suffixes added by features 5-7 (priority, tags, due)
    if task.get("priority") and task["priority"] != "medium":
        line += f" ({task['priority']})"
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    priority = "medium"
    tags = []
    due = None

    i = 0
    title_parts = []
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)

    tasks = load_tasks()
    next_id = get_next_id(tasks)

    push_history(tasks, next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks = load_tasks()
    show_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            show_tag = args[i + 1]
            i += 2
        elif args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue:
        if today_str is None:
            today = date.today().isoformat()
        else:
            today = today_str
        try:
            today_date = date.fromisoformat(today)
        except ValueError:
            print(f"Invalid date: {today}", file=sys.stderr)
            sys.exit(1)
        tasks = [
            t for t in tasks
            if not t["done"]
            and t.get("due")
            and date.fromisoformat(t["due"]) < today_date
        ]

    if show_tag:
        tasks = [t for t in tasks if show_tag in t.get("tags", [])]

    if not tasks:
        print("No tasks")
        return

    for task in sorted(tasks, key=lambda t: t["id"]):
        print(format_task_line(task))


def cmd_done(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(tasks, get_next_id(tasks))
    task["done"] = True
    save_tasks(tasks)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(tasks, get_next_id(tasks))
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid task id: {args[0]}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title", file=sys.stderr)
                sys.exit(1)
            parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            new_title = " ".join(parts)
        else:
            i += 1

    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    push_history(tasks, get_next_id(tasks))
    task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    tasks = load_tasks()
    matches = [t for t in tasks if query in t["title"].lower()]

    if not matches:
        print("No matches")
        return

    for task in sorted(matches, key=lambda t: t["id"]):
        print(format_task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None or fmt not in ("json", "csv"):
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks()

    if fmt == "json":
        output = []
        for t in sorted(tasks, key=lambda x: x["id"]):
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in sorted(tasks, key=lambda x: x["id"]):
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t['priority']},{tags_str},{due_str}")


def cmd_stats(args):
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {len(tasks)}")


def cmd_undo(args):
    tasks, next_id = pop_history()
    save_tasks(tasks)
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
    args = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[cmd](args)


if __name__ == "__main__":
    main()
