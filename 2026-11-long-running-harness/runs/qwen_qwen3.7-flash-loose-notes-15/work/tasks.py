#!/usr/bin/env python3
"""A command-line task manager using only Python 3 standard library."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_add_args(args):
    result = {"title_parts": [], "priority": None, "tags": [], "due": None}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                error("Missing value for --priority")
            result["priority"] = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                error("Missing value for --tag")
            result["tags"].append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                error("Missing value for --due")
            result["due"] = args[i + 1]
            i += 2
        else:
            result["title_parts"].append(arg)
            i += 1
    return result


def make_task_line(task):
    done_mark = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_mark} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def _deep_copy_tasks(tasks_dict):
    """Deep copy a tasks dict so mutations don't affect saved history."""
    return json.loads(json.dumps(tasks_dict))


def cmd_add(args):
    if not args:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    parsed = parse_add_args(args)
    if not parsed["title_parts"]:
        error("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = " ".join(parsed["title_parts"])
    priority = parsed["priority"]
    if priority is not None and priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")
    due = parsed["due"]
    if due is not None and not validate_date(due):
        error(f"Invalid date: {due}")
    data = load_data()
    prev_tasks = _deep_copy_tasks(data["tasks"])
    task_id = data["next_id"]
    task = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": parsed["tags"],
        "due": due,
    }
    key = str(task_id)
    data["tasks"][key] = task
    data["next_id"] += 1
    data["history"].append({
        "type": "add",
        "task_id": task_id,
        "prev_tasks": prev_tasks,
        "prev_next_id": task_id,
    })
    save_data(data)
    print(f"Added {task_id}")


def cmd_list(args):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                error(f"Unknown sort option: {args[i + 1]}")
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_str = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if overdue and not today_str:
        today_str = date.today().isoformat()
    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    filtered = tasks
    if tag_filter:
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]
    if overdue:
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")
        filtered = [t for t in filtered if not t["done"] and t.get("due")
                    and datetime.strptime(t["due"], "%Y-%m-%d").date() < today]
    if not filtered:
        print("No tasks")
        return
    if sort_priority:
        po = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    for task in filtered:
        print(make_task_line(task))


def _find_task(data, task_id):
    """Look up task by id, converting to string key."""
    key = str(task_id)
    if key not in data["tasks"]:
        error(f"No such task: {task_id}")
    return key


def cmd_done(args):
    if not args:
        error("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")
    data = load_data()
    key = _find_task(data, task_id)
    prev_tasks = _deep_copy_tasks(data["tasks"])
    data["tasks"][key]["done"] = True
    data["history"].append({
        "type": "done",
        "task_id": task_id,
        "prev_tasks": prev_tasks,
        "prev_next_id": data["next_id"],
    })
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if not args:
        error("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")
    data = load_data()
    key = _find_task(data, task_id)
    prev_tasks = _deep_copy_tasks(data["tasks"])
    prev_next_id = data["next_id"]
    del data["tasks"][key]
    data["history"].append({
        "type": "delete",
        "task_id": task_id,
        "prev_tasks": prev_tasks,
        "prev_next_id": prev_next_id,
    })
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if not args:
        error("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        error(f"Invalid id: {args[0]}")
    rest = args[1:]
    title_idx = None
    for i, arg in enumerate(rest):
        if arg == "--title":
            title_idx = i
            break
    if title_idx is None or title_idx + 1 >= len(rest):
        error("Usage: edit ID --title NEW TITLE")
    new_title = " ".join(rest[title_idx + 1:])
    data = load_data()
    key = _find_task(data, task_id)
    prev_tasks = _deep_copy_tasks(data["tasks"])
    data["tasks"][key]["title"] = new_title
    data["history"].append({
        "type": "edit",
        "task_id": task_id,
        "prev_tasks": prev_tasks,
        "prev_next_id": data["next_id"],
    })
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        error("Usage: search TEXT")
    text = " ".join(args).lower()
    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(make_task_line(task))


def cmd_export(args):
    if not args:
        error("Usage: export --format json|csv")
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            error(f"Unknown option: {args[i]}")
    if fmt not in ("json", "csv"):
        error(f"Unknown format: {fmt}")
    data = load_data()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for task in tasks:
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task["priority"],
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for task in tasks:
            tags_str = ";".join(task.get("tags", []))
            due_str = task.get("due") or ""
            print(f"{task['id']},{task['title']},{str(task['done']).lower()},{task['priority']},{tags_str},{due_str}")


def cmd_stats(args):
    data = load_data()
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    data = load_data()
    if not data["history"]:
        error("Nothing to undo")
    snapshot = data["history"].pop()
    data["tasks"] = snapshot["prev_tasks"]
    data["next_id"] = snapshot["prev_next_id"]
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
        error("Usage: python3 tasks.py <command> [args]")
    command = sys.argv[1]
    if command not in COMMANDS:
        error(f"Unknown command: {command}")
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
