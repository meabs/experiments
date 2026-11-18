#!/usr/bin/env python3
"""Command-line task manager. Python 3 standard library only."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", [])
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def load_undo_history():
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def next_id(tasks):
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    tags = task.get("tags", [])
    if tags:
        parts.extend(tags)
    due = task.get("due")
    if due:
        parts.append(f"due:{due}")
    return " ".join(parts)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


# ── Commands (argv = sys.argv[2:], i.e., args after command name) ─

def cmd_add(args):
    """add TITLE [--priority high|medium|low] [--tag TAG]... [--due DATE]"""
    tasks = load_tasks()
    history = load_undo_history()
    nid = next_id(tasks)

    priority = None
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "--priority":
            i += 1; priority = args[i]
        elif tok == "--tag":
            i += 1; tags.append(args[i])
        elif tok == "--due":
            i += 1; due = args[i]
        else:
            title_parts.append(tok)
        i += 1

    if not title_parts:
        error("Missing title")

    if priority is not None and priority not in ("high", "medium", "low"):
        error(f"Invalid priority: {priority}")
    if due is not None:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            error(f"Invalid date: {due}")

    new_task = {"id": nid, "title": " ".join(title_parts), "done": False,
                "priority": priority or "medium", "tags": tags, "due": due}

    history.append({"type": "add", "task_id": nid})
    save_undo_history(history)
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Added {nid}")


def cmd_list(args):
    """list [--sort priority] [--tag TAG] [--overdue] [--today YYYY-MM-DD]"""
    tasks = load_tasks()
    if not tasks:
        print("No tasks")
        return

    tag_filter = None
    sort_mode = None
    show_overdue = False
    today_str = None
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "--tag" and i + 1 < len(args):
            tag_filter = args[i+1]; i += 2
        elif tok == "--sort" and i + 1 < len(args):
            sort_mode = args[i+1]; i += 2
        elif tok == "--overdue":
            show_overdue = True; i += 1
        elif tok == "--today" and i + 1 < len(args):
            today_str = args[i+1]; i += 2
        else:
            i += 1

    filtered = []
    today = date.today()
    if today_str:
        try:
            today = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")

    for t in tasks:
        if tag_filter and tag_filter not in t.get("tags", []):
            continue
        if show_overdue:
            if t["done"]:
                continue
            d = t.get("due")
            if not d:
                continue
            dd = datetime.strptime(d, "%Y-%m-%d").date()
            if dd >= today:
                continue
        filtered.append(t)

    if sort_mode == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda x: (po.get(x.get("priority","medium"),1), x["id"]))
    else:
        filtered.sort(key=lambda x: x["id"])

    if not filtered:
        print("No tasks")
        return
    for t in filtered:
        print(task_line(t))


def cmd_done(args):
    """done ID"""
    tasks = load_tasks()
    if not args:
        error("Missing task ID")
    tid = int(args[0])
    task = next((t for t in tasks if t["id"] == tid), None)
    if task is None:
        error(f"No such task: {tid}")
    history = load_undo_history()
    history.append({"type": "done", "task_id": tid, "prev_done": task["done"]})
    save_undo_history(history)
    task["done"] = True
    save_tasks(tasks)
    print(f"Done {tid}")


def cmd_delete(args):
    """delete ID"""
    tasks = load_tasks()
    if not args:
        error("Missing task ID")
    tid = int(args[0])
    task = next((t for t in tasks if t["id"] == tid), None)
    if task is None:
        error(f"No such task: {tid}")
    history = load_undo_history()
    history.append({"type": "delete", "task_id": tid, "task_data": task})
    save_undo_history(history)
    tasks.remove(task)
    save_tasks(tasks)
    print(f"Deleted {tid}")


def cmd_edit(args):
    """edit ID --title NEW TITLE"""
    tasks = load_tasks()
    if not args:
        error("Missing task ID")
    tid = int(args[0])
    task = next((t for t in tasks if t["id"] == tid), None)
    if task is None:
        error(f"No such task: {tid}")

    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            i += 1
            parts = []
            while i < len(args):
                parts.append(args[i]); i += 1
            new_title = " ".join(parts)
            break
        i += 1

    if new_title is None:
        error("--title is required for edit")

    history = load_undo_history()
    history.append({"type": "edit", "task_id": tid, "prev_title": task["title"]})
    save_undo_history(history)
    task["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {tid}")


def cmd_search(args):
    """search TEXT"""
    tasks = load_tasks()
    if not args:
        error("Missing search text")
    query = args[0].lower()
    matches = sorted([t for t in tasks if query in t["title"].lower()], key=lambda x: x["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args):
    """export --format json|csv"""
    tasks = load_tasks()
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i+1]; i += 2
        else:
            i += 1
    if not fmt:
        error("--format is required")
    tasks_sorted = sorted(tasks, key=lambda x: x["id"])

    if fmt == "json":
        out = []
        for t in tasks_sorted:
            out.append({"id": t["id"], "title": t["title"], "done": t["done"],
                        "priority": t["priority"], "tags": t.get("tags",[]),
                        "due": t.get("due")})
        print(json.dumps(out))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks_sorted:
            done_s = "true" if t["done"] else "false"
            tags_s = ";".join(t.get("tags", []))
            due_s = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_s},{t['priority']},{tags_s},{due_s}")
    else:
        error(f"Invalid format: {fmt}")


def cmd_stats(args):
    """stats"""
    tasks = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """undo"""
    history = load_undo_history()
    if not history:
        error("Nothing to undo")

    entry = history.pop()
    save_undo_history(history)
    tasks = load_tasks()

    if entry["type"] == "add":
        tid = entry["task_id"]
        tasks = [t for t in tasks if t["id"] != tid]
    elif entry["type"] == "delete":
        tasks.append(entry["task_data"])
    elif entry["type"] == "done":
        tid = entry["task_id"]
        for t in tasks:
            if t["id"] == tid:
                t["done"] = entry["prev_done"]
                break
    elif entry["type"] == "edit":
        tid = entry["task_id"]
        for t in tasks:
            if t["id"] == tid:
                t["title"] = entry["prev_title"]
                break

    save_tasks(tasks)
    print("Undone")


# ── Main ──────────────────────────────────────────────────────────

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
        error("No command provided")
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        error(f"Unknown command: {cmd}")
    args = sys.argv[2:]
    COMMANDS[cmd](args)


if __name__ == "__main__":
    main()
