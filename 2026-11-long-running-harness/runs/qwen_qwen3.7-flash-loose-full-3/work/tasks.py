#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date

DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = {t["id"]: t for t in data.get("tasks", [])}
    return tasks, data.get("next_id", 1)


def save_tasks(tasks, next_id):
    data = {"tasks": list(tasks.values()), "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def push_undo(tasks, next_id):
    history = load_undo_history()
    snapshot = ({tid: dict(t) for tid, t in tasks.items()}, next_id)
    history.append(snapshot)
    save_undo_history(history)


def undo_last():
    history = load_undo_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = history.pop()
    save_undo_history(history)
    save_tasks(tasks, next_id)
    print("Undone")


def format_task_line(task):
    prefix = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {prefix} {task['title']}"
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{tag}" for tag in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def parse_args(args):
    if not args:
        return {}
    opts = {"positional": [], "_raw_tags": []}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            opts["priority"] = args[i + 1]
            i += 2
        elif a == "--tag":
            if i + 1 >= len(args):
                print("Error: --tag requires a value", file=sys.stderr)
                sys.exit(1)
            opts["_raw_tags"].append(args[i + 1])
            i += 2
        elif a == "--due":
            if i + 1 >= len(args):
                print("Invalid date: ", file=sys.stderr)
                sys.exit(1)
            opts["due"] = args[i + 1]
            i += 2
        elif a == "--title":
            if i + 1 >= len(args):
                print("Error: --title requires a value", file=sys.stderr)
                sys.exit(1)
            opts["title"] = args[i + 1]
            i += 2
        elif a == "--format":
            if i + 1 >= len(args):
                print("Error: --format requires a value", file=sys.stderr)
                sys.exit(1)
            opts["format"] = args[i + 1]
            i += 2
        elif a == "--sort":
            if i + 1 >= len(args):
                print("Error: --sort requires a value", file=sys.stderr)
                sys.exit(1)
            opts["sort"] = args[i + 1]
            i += 2
        elif a == "--overdue":
            opts["overdue"] = True
            i += 1
        elif a == "--today":
            if i + 1 >= len(args):
                print("Error: --today requires a value", file=sys.stderr)
                sys.exit(1)
            opts["today"] = args[i + 1]
            i += 2
        else:
            opts["positional"].append(a)
            i += 1
    return opts


def validate_date(date_str):
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return False
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
        return True
    except (ValueError, IndexError):
        return False


def cmd_add(args):
    tasks, next_id = load_tasks()
    positional = args.get("positional", [])
    if not positional:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(positional)
    priority = args.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)
    tags = args.get("_raw_tags", [])
    due = args.get("due", None)
    if due is not None and not validate_date(due):
        print(f"Invalid date: {due}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks[next_id] = task
    save_tasks(tasks, next_id + 1)
    print(f"Added {next_id}")


def cmd_list(args):
    tasks, _ = load_tasks()
    sort_by = args.get("sort", None)
    overdue = args.get("overdue", False)
    today_str = args.get("today", None)
    raw_tags = args.get("_raw_tags", [])
    tag_filter = None
    if raw_tags and not args.get("positional"):
        tag_filter = raw_tags[0]
    task_list = sorted(tasks.values(), key=lambda t: t["id"])
    if overdue:
        today_date = date.today()
        if today_str:
            try:
                parts = today_str.split("-")
                today_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                print(f"Invalid date: {today_str}", file=sys.stderr)
                sys.exit(1)
        filtered = []
        for t in task_list:
            if not t["done"] and t.get("due"):
                try:
                    dp = t["due"].split("-")
                    dd = date(int(dp[0]), int(dp[1]), int(dp[2]))
                    if dd < today_date:
                        filtered.append(t)
                except ValueError:
                    continue
        task_list = filtered
    if tag_filter:
        task_list = [t for t in task_list if tag_filter in t.get("tags", [])]
    if sort_by == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        task_list.sort(key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    if not task_list:
        print("No tasks")
    else:
        for t in task_list:
            print(format_task_line(t))


def cmd_done(args):
    tasks, next_id = load_tasks()
    positional = args.get("positional", [])
    if not positional:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print(f"No such task: {positional[0]}", file=sys.stderr)
        sys.exit(1)
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(args):
    tasks, next_id = load_tasks()
    positional = args.get("positional", [])
    if not positional:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print(f"No such task: {positional[0]}", file=sys.stderr)
        sys.exit(1)
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    tasks, next_id = load_tasks()
    positional = args.get("positional", [])
    if not positional:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print(f"No such task: {positional[0]}", file=sys.stderr)
        sys.exit(1)
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    new_title = args.get("title")
    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(args):
    tasks, _ = load_tasks()
    positional = args.get("positional", [])
    if not positional:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(positional).lower()
    matches = [t for t in tasks.values() if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
    else:
        for t in matches:
            print(format_task_line(t))


def cmd_export(args):
    tasks, _ = load_tasks()
    fmt = args.get("format", "")
    if fmt not in ("json", "csv"):
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)
    task_list = sorted(tasks.values(), key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in task_list:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in task_list:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            priority_str = t.get("priority", "medium")
            print(f"{t['id']},{t['title']},{done_str},{priority_str},{tags_str},{due_str}")


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "undo":
        undo_last()
    elif cmd in COMMANDS:
        opts = parse_args(sys.argv[2:])
        COMMANDS[cmd](opts)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
