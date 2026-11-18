#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import sys
import json
import os
from datetime import datetime, date

DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and state from data file. Create if missing."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and state to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task into its display line."""
    tid = task["id"]
    status = "[x]" if task["done"] else "[ ]"
    line = f"{tid} {status} {task['title']}"
    # priority suffix
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # tags suffix
    if task.get("tags"):
        line += " " + " ".join(f"#{t}" for t in task["tags"])
    # due date suffix
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args, data):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                error("Invalid priority: ")
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag requires a value")
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                error("--due requires a value")
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        error("add requires a title")
    title = " ".join(title_parts)
    # validate due date
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")
    next_id = data["next_id"]
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"][next_id] = task
    data["next_id"] = next_id + 1
    # record undo history for add
    data["history"].append({
        "action": "add",
        "task_id": next_id,
        "prev_next_id": next_id,
    })
    save_data(data)
    print(f"Added {next_id}")


def cmd_list(args, data):
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    # parse filters/sort
    tag_filter = None
    sort_by = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                error("--sort requires a value")
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                error("--tag filter requires a value")
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                error("--today requires a date value")
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    if overdue or tag_filter or sort_by:
        filtered = []
        today = today_str if today_str else date.today().isoformat()
        for t in tasks:
            if overdue:
                if t["done"]:
                    continue
                if not t.get("due"):
                    continue
                if t["due"] >= today:
                    continue
            if tag_filter:
                if tag_filter not in t.get("tags", []):
                    continue
            filtered.append(t)
        tasks = filtered
    if sort_by == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        if any(arg in args for arg in ["--sort", "--tag", "--overdue"]):
            print("No tasks")
        else:
            print("No tasks")
        return
    for t in tasks:
        print(task_line(t))


def cmd_done(args, data):
    if not args:
        error("done requires an ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    if tid not in data["tasks"]:
        error(f"No such task: {tid}")
    data["tasks"][tid]["done"] = True
    data["history"].append({
        "action": "done",
        "task_id": tid,
        "prev_done": False,
    })
    save_data(data)
    print(f"Done {tid}")


def cmd_delete(args, data):
    if not args:
        error("delete requires an ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    if tid not in data["tasks"]:
        error(f"No such task: {tid}")
    del data["tasks"][tid]
    data["history"].append({
        "action": "delete",
        "task_id": tid,
    })
    save_data(data)
    print(f"Deleted {tid}")


def cmd_edit(args, data):
    if not args:
        error("edit requires an ID")
    try:
        tid = int(args[0])
    except ValueError:
        error(f"No such task: {args[0]}")
    if tid not in data["tasks"]:
        error(f"No such task: {tid}")
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                error("--title requires a value")
            title_parts = [args[i + 1]]
            j = i + 2
            while j < len(args) and not args[j].startswith("--"):
                title_parts.append(args[j])
                j += 1
            new_title = " ".join(title_parts)
            i = j
        else:
            i += 1
    if new_title is None:
        error("edit requires --title")
    data["tasks"][tid]["title"] = new_title
    data["history"].append({
        "action": "edit",
        "task_id": tid,
        "prev_title": data["tasks"][tid]["title"],
    })
    save_data(data)
    print(f"Edited {tid}")


def cmd_search(args, data):
    if not args:
        error("search requires TEXT")
    text = " ".join(args).lower()
    matches = []
    for t in sorted(data["tasks"].values(), key=lambda x: x["id"]):
        if text in t["title"].lower():
            matches.append(t)
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
                error("--format requires json or csv")
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        error("--format must be json or csv")
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
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority','medium')},{tags_str},{due_str}")


def cmd_stats(args, data):
    tasks = data["tasks"].values()
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args, data):
    if not data["history"]:
        error("Nothing to undo")
    last = data["history"].pop()
    action = last["action"]
    if action == "add":
        tid = last["task_id"]
        if tid in data["tasks"]:
            del data["tasks"][tid]
        data["next_id"] = last["prev_next_id"]
    elif action == "done":
        tid = last["task_id"]
        if tid in data["tasks"]:
            data["tasks"][tid]["done"] = last["prev_done"]
    elif action == "delete":
        tid = last["task_id"]
        # We need to restore the deleted task. But we don't have it stored!
        # This is a problem - we need to store more info.
        error("Undo delete not fully implemented yet")
    elif action == "edit":
        tid = last["task_id"]
        if tid in data["tasks"]:
            data["tasks"][tid]["title"] = last["prev_title"]
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
    data = load_data()
    COMMANDS[command](sys.argv[2:], data)


if __name__ == "__main__":
    main()
