#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import re
import sys


DATA_FILE = os.path.join(os.getcwd(), "tasks.json")


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        for key in ("next_id", "tasks", "history"):
            if key not in data:
                data[key] = {"next_id": 1, "tasks": [], "history": []}[key]
        return data
    except (json.JSONDecodeError, IOError):
        return {"next_id": 1, "tasks": [], "history": []}


def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def push_history(data):
    data["history"].append({"next_id": data["next_id"], "tasks": [dict(t) for t in data["tasks"]]})


def find_task(data, task_id):
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            return i, t
    return None, None


def validate_date(date_str):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        p = date_str.split("-")
        import datetime
        datetime.date(int(p[0]), int(p[1]), int(p[2]))
        return True
    except ValueError:
        return False


def task_line(task):
    status = "x" if task["done"] else " "
    line = f"{task['id']} [{status}] {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def cmd_add(args, data):
    if not args:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG] [--due YYYY-MM-DD]", file=sys.stderr)
        return
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                return
            i += 1
            priority = args[i]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                return
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                return
            i += 1
            tags.append(args[i])
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                return
            i += 1
            due = args[i]
            if not validate_date(due):
                print(f"Invalid date: {due}", file=sys.stderr)
                return
        else:
            title_parts.append(arg)
        i += 1
    if not title_parts:
        print("Missing task title", file=sys.stderr)
        return
    title = " ".join(title_parts)
    push_history(data)
    task_id = data["next_id"]
    data["next_id"] += 1
    task = {"id": task_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    data["tasks"].append(task)
    save(data)
    print(f"Added {task_id}")


def cmd_list(args, data):
    import datetime
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                return
            i += 1
            if args[i] == "priority":
                sort_priority = True
            else:
                print(f"Unknown sort option: {args[i]}", file=sys.stderr)
                return
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                return
            i += 1
            tag_filter = args[i]
        elif arg == "--overdue":
            overdue = True
        elif arg == "--today":
            if i + 1 >= len(args):
                print("Missing value for --today", file=sys.stderr)
                return
            i += 1
            today_str = args[i]
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            return
        i += 1
    today = datetime.date.fromisoformat(today_str) if today_str else datetime.date.today()
    tasks = list(data["tasks"])
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    dd = datetime.date.fromisoformat(t["due"])
                    if dd < today:
                        filtered.append(t)
                except ValueError:
                    continue
        tasks = filtered
    if sort_priority:
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        return
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid ID: {args[0]}", file=sys.stderr)
        return
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return
    push_history(data)
    task["done"] = True
    save(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        return
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid ID: {args[0]}", file=sys.stderr)
        return
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return
    push_history(data)
    data["tasks"].pop(idx)
    save(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        return
    try:
        task_id = int(args[0])
    except ValueError:
        print(f"Invalid ID: {args[0]}", file=sys.stderr)
        return
    idx, task = find_task(data, task_id)
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        return
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing value for --title", file=sys.stderr)
                return
            i += 1
            # Collect all remaining arguments as the title
            new_title = " ".join(args[i:])
            break
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            return
        i += 1
    if new_title is None:
        print("--title is required", file=sys.stderr)
        return
    push_history(data)
    task["title"] = new_title
    save(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        return
    text = " ".join(args).lower()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing value for --format", file=sys.stderr)
                return
            i += 1
            fmt = args[i]
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            return
        i += 1
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        return
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        output = [{"id": t["id"], "title": t["title"], "done": t["done"], "priority": t.get("priority", "medium"), "tags": t.get("tags", []), "due": t.get("due")} for t in tasks]
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            print(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t.get('priority','medium')},{';'.join(t.get('tags',[]))},{t.get('due','')}")
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)


def cmd_stats(args, data):
    oc = sum(1 for t in data["tasks"] if not t["done"])
    dc = sum(1 for t in data["tasks"] if t["done"])
    tc = len(data["tasks"])
    print(f"open: {oc}")
    print(f"done: {dc}")
    print(f"total: {tc}")


def cmd_undo(args, data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        return
    prev = data["history"].pop()
    data["next_id"] = prev["next_id"]
    data["tasks"] = prev["tasks"]
    save(data)
    print("Undone")


COMMANDS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete, "edit": cmd_edit, "search": cmd_search, "export": cmd_export, "stats": cmd_stats, "undo": cmd_undo}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    data = load()
    result = COMMANDS[command](args, data)
    if result is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
