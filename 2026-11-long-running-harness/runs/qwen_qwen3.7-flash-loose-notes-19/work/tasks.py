#!/usr/bin/env python3
"""A command-line task manager."""

import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def format_task(t):
    c = "x" if t["done"] else " "
    line = str(t["id"]) + " [" + c + "] " + t["title"]
    p = t.get("priority", "medium")
    if p == "high":
        line += " (high)"
    elif p == "low":
        line += " (low)"
    tags = t.get("tags", [])
    if tags:
        line += " " + " ".join("#" + g for g in tags)
    if t.get("due"):
        line += " due:" + t["due"]
    return line


def cmd_add(args):
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
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: " + priority, file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            ds = args[i + 1]
            try:
                datetime.strptime(ds, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: " + ds, file=sys.stderr)
                sys.exit(1)
            due = ds
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    tasks.append(task)
    new_next = next_id + 1
    undo_history = load_undo()
    undo_history.append({"tasks": tasks[:-1], "next_id": next_id})
    save_undo(undo_history)
    save_tasks(tasks, new_next)
    print("Added " + str(next_id))


def cmd_list(args):
    tasks, next_id = load_tasks()
    if not tasks:
        print("No tasks")
        return
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
                print("Unknown sort option: " + args[i + 1], file=sys.stderr)
                sys.exit(1)
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
            i += 1
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        today = date.fromisoformat(today_str) if today_str else date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]
    if sort_priority:
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    for task in tasks:
        print(format_task(task))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid id: " + args[0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break
    if not found:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    undo_history = load_undo()
    prev = [{"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"],
             "tags": list(t["tags"]), "due": t["due"]} for t in tasks]
    undo_history.append({"tasks": prev, "next_id": next_id})
    save_undo(undo_history)
    found["done"] = True
    save_tasks(tasks, next_id)
    print("Done " + str(tid))


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid id: " + args[0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break
    if not found:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    tasks = [t for t in tasks if t["id"] != tid]
    undo_history = load_undo()
    undo_history.append({"tasks": tasks, "next_id": next_id})
    save_undo(undo_history)
    save_tasks(tasks, next_id)
    print("Deleted " + str(tid))


def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid id: " + args[0], file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing value for --title", file=sys.stderr)
                sys.exit(1)
            parts = []
            j = i + 1
            while j < len(args) and not args[j].startswith("--"):
                parts.append(args[j])
                j += 1
            if not parts:
                print("Empty title", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(parts)
            i = j
        else:
            i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break
    if not found:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    undo_history = load_undo()
    prev = [{"id": t["id"], "title": t["title"], "done": t["done"], "priority": t["priority"],
             "tags": list(t["tags"]), "due": t["due"]} for t in tasks]
    undo_history.append({"tasks": prev, "next_id": next_id})
    save_undo(undo_history)
    found["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited " + str(tid))


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    tasks, next_id = load_tasks()
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    if fmt not in ("json", "csv"):
        print("Invalid format: " + fmt, file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if fmt == "json":
        out = []
        for t in tasks:
            out.append({"id": t["id"], "title": t["title"], "done": t["done"],
                        "priority": t.get("priority", "medium"),
                        "tags": t.get("tags", []), "due": t.get("due")})
        print(json.dumps(out, indent=2))
    else:
        print("id,title,done,priority,tags,due")
        for t in tasks:
            ts = ";".join(t.get("tags", []))
            ds = t.get("due") or ""
            print(str(t["id"]) + "," + t["title"] + "," + ("true" if t["done"] else "false") + "," + t.get("priority", "medium") + "," + ts + "," + ds)


def cmd_stats(args):
    tasks, next_id = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total))


def cmd_undo(args):
    history = load_undo()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = history.pop()
    save_undo(history)
    save_tasks(state["tasks"], state["next_id"])
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
        print("Unknown command: " + cmd_name, file=sys.stderr)
        sys.exit(1)
    COMMANDS[cmd_name](sys.argv[2:])


if __name__ == "__main__":
    main()
