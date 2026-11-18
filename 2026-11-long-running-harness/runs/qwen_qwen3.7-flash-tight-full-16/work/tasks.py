#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks from the data file, or return empty state."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": {}, "next_id": 1, "undo_stack": []}


def save_data(data):
    """Save tasks to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def add_task(args, data):
    """Handle 'add' command."""
    if not args:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

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
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    title = " ".join(title_parts)
    next_id = data["next_id"]

    # Save state for undo before mutation
    data["undo_stack"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"]
    }))

    data["tasks"][str(next_id)] = {
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due
    }
    data["next_id"] = next_id + 1
    save_data(data)
    print(f"Added {next_id}")


def format_task(task_id, task):
    """Format a task for display."""
    status = "[x]" if task["done"] else "[ ]"
    line = f"{task_id} {status} {task['title']}"
    if task["priority"] in ("high", "low"):
        line += f" ({task['priority']})"
    if task["tags"]:
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task["due"]:
        line += f" due:{task['due']}"
    return line


def list_tasks(args, data):
    """Handle 'list' command."""
    sort_priority = False
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires a value", file=sys.stderr)
                sys.exit(1)
            sort_option = args[i + 1]
            if sort_option == "priority":
                sort_priority = True
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires a date", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1

    import datetime
    if today is None:
        today_str = datetime.date.today().isoformat()
    else:
        today_str = today
    today_date = datetime.date.fromisoformat(today_str)

    tasks = data["tasks"]
    if not tasks:
        print("No tasks")
        return

    result = []
    for tid, task in sorted(tasks.items(), key=lambda x: int(x[0])):
        # Filter by tag if specified
        if tag_filter and tag_filter not in task["tags"]:
            continue
        # Filter overdue: only open tasks due before today
        if overdue:
            if task["done"]:
                continue
            if not task["due"]:
                continue
            try:
                due_date = datetime.date.fromisoformat(task["due"])
            except ValueError:
                continue
            if due_date >= today_date:
                continue
        result.append((int(tid), task))

    if not result:
        print("No tasks")
        return

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda x: (priority_order.get(x[1]["priority"], 1), x[0]))

    for tid, task in result:
        print(format_task(str(tid), task))


def done_task(args, data):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    task_id = args[0]
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    data["undo_stack"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"]
    }))

    data["tasks"][task_id]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def delete_task(args, data):
    """Handle 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    task_id = args[0]
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    data["undo_stack"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"]
    }))

    del data["tasks"][task_id]
    save_data(data)
    print(f"Deleted {task_id}")


def edit_task(args, data):
    """Handle 'edit' command."""
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task_id = args[0]
    if task_id not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            j = i + 1
            while j < len(args) and not args[j].startswith("--"):
                title_parts.append(args[j])
                j += 1
            new_title = " ".join(title_parts)
            i = j
        else:
            i += 1

    if new_title is None:
        print("--title is required", file=sys.stderr)
        sys.exit(1)

    data["undo_stack"].append(json.dumps({
        "tasks": data["tasks"],
        "next_id": data["next_id"]
    }))

    data["tasks"][task_id]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def search_tasks(args, data):
    """Handle 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    results = []
    for tid, task in sorted(data["tasks"].items(), key=lambda x: int(x[0])):
        if query in task["title"].lower():
            results.append((tid, task))

    if not results:
        print("No matches")
        return

    for tid, task in results:
        print(format_task(tid, task))


def export_tasks(args, data):
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

    if fmt is None:
        print("--format is required", file=sys.stderr)
        sys.exit(1)

    tasks_list = []
    for tid in sorted(data["tasks"].keys(), key=lambda x: int(x)):
        task = data["tasks"][tid]
        tasks_list.append({
            "id": int(tid),
            "title": task["title"],
            "done": task["done"],
            "priority": task["priority"],
            "tags": task["tags"],
            "due": task["due"]
        })

    if fmt == "json":
        print(json.dumps(tasks_list, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks_list:
            done_str = "true" if task["done"] else "false"
            tags_str = ";".join(task["tags"]) if task["tags"] else ""
            due_str = task["due"] if task["due"] else ""
            print(f"{task['id']},{task['title']},{done_str},{task['priority']},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def stats_cmd(args, data):
    """Handle 'stats' command."""
    tasks = data["tasks"]
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def undo_cmd(args, data):
    """Handle 'undo' command."""
    if not data["undo_stack"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    prev_state = json.loads(data["undo_stack"].pop())
    data["tasks"] = prev_state["tasks"]
    data["next_id"] = prev_state["next_id"]
    save_data(data)
    print("Undone")


COMMANDS = {
    "add": add_task,
    "list": list_tasks,
    "done": done_task,
    "delete": delete_task,
    "edit": edit_task,
    "search": search_tasks,
    "export": export_tasks,
    "stats": stats_cmd,
    "undo": undo_cmd,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](args, data)


if __name__ == "__main__":
    main()
