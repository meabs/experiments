#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def format_task(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    if task.get("tags"):
        for tag in task["tags"]:
            parts.append(f"#{tag}")
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args, data):
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Missing priority value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
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
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    title = " ".join(title_parts)
    task_id = data["next_id"]
    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority if priority else "medium",
        "tags": tags,
        "due": due,
    }
    data["next_id"] = task_id + 1
    data["history"].append({
        "type": "add",
        "task_id": task_id,
        "task": dict(data["tasks"][task_id]),
    })
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
        elif args[i] == "--tag" and i + 1 < len(args):
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

    if overdue and today_str is None:
        today_str = date.today().isoformat()

    tasks = list(data["tasks"].values())
    if filter_tag:
        tasks = [t for t in tasks if filter_tag in t.get("tags", [])]
    if overdue:
        today = datetime.strptime(today_str, "%Y-%m-%d").date()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and
                 datetime.strptime(t["due"], "%Y-%m-%d").date() < today]
    if sort_priority:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
    else:
        for task in tasks:
            print(format_task(task))


def cmd_done(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if str(task_id) not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    old_task = dict(data["tasks"][str(task_id)])
    data["history"].append({
        "type": "done",
        "task_id": task_id,
        "old_task": old_task,
        "new_state": {"done": True},
    })
    data["tasks"][str(task_id)]["done"] = True
    save_data(data)
    print(f"Done {task_id}")


def cmd_delete(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    task_id = int(args[0])
    if str(task_id) not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    old_task = dict(data["tasks"][str(task_id)])
    data["history"].append({
        "type": "delete",
        "task_id": task_id,
        "task": old_task,
        "next_id_before": data["next_id"],
    })
    del data["tasks"][str(task_id)]
    save_data(data)
    print(f"Deleted {task_id}")


def cmd_edit(args, data):
    task_id = None
    new_title = None
    i = 0
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title value", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            if task_id is None:
                try:
                    task_id = int(args[i])
                except ValueError:
                    pass
            i += 1

    if task_id is None or new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    if str(task_id) not in data["tasks"]:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)

    old_task = dict(data["tasks"][str(task_id)])
    data["history"].append({
        "type": "edit",
        "task_id": task_id,
        "old_task": old_task,
        "new_title": new_title,
    })
    data["tasks"][str(task_id)]["title"] = new_title
    save_data(data)
    print(f"Edited {task_id}")


def cmd_search(args, data):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    matches = []
    for task in sorted(data["tasks"].values(), key=lambda t: t["id"]):
        if query in task["title"].lower():
            matches.append(task)
    if not matches:
        print("No matches")
    else:
        for task in matches:
            print(format_task(task))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        print(f"Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        export_data = []
        for t in tasks:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    open_count = sum(1 for t in data["tasks"].values() if not t["done"])
    done_count = sum(1 for t in data["tasks"].values() if t["done"])
    total = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    entry = data["history"].pop()
    hist_type = entry["type"]
    if hist_type == "add":
        task_id = entry["task_id"]
        if str(task_id) in data["tasks"]:
            del data["tasks"][str(task_id)]
        data["next_id"] = task_id
    elif hist_type == "done":
        task_id = entry["task_id"]
        if str(task_id) in data["tasks"]:
            data["tasks"][str(task_id)]["done"] = entry["old_task"]["done"]
    elif hist_type == "delete":
        task_id = entry["task_id"]
        data["tasks"][str(task_id)] = entry["task"]
        data["next_id"] = entry["next_id_before"]
    elif hist_type == "edit":
        task_id = entry["task_id"]
        if str(task_id) in data["tasks"]:
            data["tasks"][str(task_id)]["title"] = entry["old_task"]["title"]
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
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    cmd_name = sys.argv[1]
    if cmd_name not in COMMANDS:
        print(f"Unknown command: {cmd_name}", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    args = sys.argv[2:]
    COMMANDS[cmd_name](args, data)


if __name__ == "__main__":
    main()
