#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def snapshot(data):
    import copy
    return copy.deepcopy(data)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = f'{task["id"]} {status} {task["title"]}'
    # priority suffix
    prio = task.get("priority", "medium")
    if prio == "high":
        line += " (high)"
    elif prio == "low":
        line += " (low)"
    # tags suffix
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    # due date suffix
    if task.get("due"):
        line += f' due:{task["due"]}'
    return line


def validate_date(date_str):
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        import datetime
        datetime.date(y, m, d)
    except (ValueError, OverflowError):
        print(f"Invalid date: {date_str}", file=sys.stderr)
        sys.exit(1)


def cmd_add(args, data):
    priority = None
    tags = []
    due = None
    title_parts = []
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
            due = args[i + 1]
            validate_date(due)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1

    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    snap = snapshot(data)
    task_id = data["next_id"]
    data["next_id"] += 1

    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["history"].append({"type": "add", "snapshot": snap})
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
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

    tasks = list(data["tasks"])

    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]

    if overdue:
        if today_str is None:
            import datetime
            today_str = datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]

    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(task_line(task))


def cmd_done(args, data):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    snap = snapshot(data)
    task["done"] = True
    data["history"].append({"type": "done", "snapshot": snap, "task_id": task_id})
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    snap = snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    data["history"].append({"type": "delete", "snapshot": snap, "task_id": task_id})
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
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
            while i < len(args) and args[i] != "--title":
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
            break
        i += 1

    if new_title is None:
        print("--title required", file=sys.stderr)
        sys.exit(1)

    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    snap = snapshot(data)
    old_title = task["title"]
    task["title"] = new_title
    data["history"].append({"type": "edit", "snapshot": snap, "task_id": task_id, "old_title": old_title})
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"], key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(task_line(task))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt:
        print("--format required", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        lines = ["id,title,done,priority,tags,due"]
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            lines.append(f'{t["id"]},{t["title"]},{str(t["done"]).lower()},{t.get("priority","medium")},{tags_str},{due_str}')
        print("\n".join(lines))
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, data):
    total = len(data["tasks"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    last_action = data["history"].pop()
    restore_snap = last_action["snapshot"]

    data["tasks"] = restore_snap["tasks"]
    data["next_id"] = restore_snap["next_id"]

    save_data(data)
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

    handler = commands.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    handler(args, data)


if __name__ == "__main__":
    main()
