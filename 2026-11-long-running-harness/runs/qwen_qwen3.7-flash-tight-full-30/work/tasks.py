#!/usr/bin/env python3
"""Command-line task manager."""
import json, os, sys
from datetime import date

DATA_FILE = "tasks.json"
HISTORY_FILE = ".tasks_history.json"

def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def record_undo(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)

def undo():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous = history.pop()
    save_tasks(previous["tasks"])
    save_history(history)
    with open(".tasks_next_id", "w") as f:
        json.dump(previous["next_id"], f)
    print("Undone")

def load_next_id():
    if os.path.exists(".tasks_next_id"):
        try:
            with open(".tasks_next_id") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    tasks = load_tasks()
    if tasks:
        return max(t["id"] for t in tasks) + 1
    return 1

def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#" + t for t in tags)
    due = task.get("due")
    if due:
        line += " due:" + due
    return line

def cmd_add(args):
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            val = args[i + 1]
            if val not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(val), file=sys.stderr)
                sys.exit(1)
            priority = val
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires value", file=sys.stderr)
                sys.exit(1)
            val = args[i + 1]
            try:
                date.fromisoformat(val)
            except ValueError:
                print("Invalid date: {}".format(val), file=sys.stderr)
                sys.exit(1)
            due = val
            i += 2
        else:
            if title is None:
                title = args[i]
            else:
                title += " " + args[i]
            i += 1
    if title is None:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    next_id = load_next_id()
    task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    tasks.append(task)
    save_tasks(tasks)
    record_undo(tasks, next_id)
    with open(".tasks_next_id", "w") as f:
        json.dump(next_id + 1, f)
    print("Added {}".format(next_id))

def cmd_list(args):
    tasks = load_tasks()
    sort_by = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("--sort requires value", file=sys.stderr)
                sys.exit(1)
            sort_by = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("--today requires value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            i += 1
    if not tasks:
        print("No tasks")
        return
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today_str:
            today = date.fromisoformat(today_str)
        else:
            today = date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]
    if sort_by == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))

def cmd_done(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    record_undo(tasks, load_next_id())
    print("Done {}".format(task_id))

def cmd_delete(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    save_tasks(new_tasks)
    record_undo(tasks, load_next_id())
    print("Deleted {}".format(task_id))

def cmd_edit(args):
    if not args:
        print("Missing task ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires value", file=sys.stderr)
                sys.exit(1)
            new_title = " ".join(args[i + 1:])
            break
        i += 1
    if new_title is None:
        print("--title is required", file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_title
            found = True
            break
    if not found:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    save_tasks(tasks)
    record_undo(tasks, load_next_id())
    print("Edited {}".format(task_id))

def cmd_search(args):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()
    tasks = load_tasks()
    matches = [t for t in tasks if search_text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))

def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("--format requires value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt not in ("json", "csv"):
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)
    tasks = load_tasks()
    tasks.sort(key=lambda t: t["id"])
    if fmt == "json":
        data = [{"id": t["id"], "title": t["title"], "done": t["done"], "priority": t.get("priority", "medium"), "tags": t.get("tags", []), "due": t.get("due")} for t in tasks]
        print(json.dumps(data))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            ts = ";".join(t.get("tags", []))
            ds = t.get("due") or ""
            dstr = "true" if t["done"] else "false"
            print("{},{},{},{},{},{}".format(t["id"], t["title"], dstr, t.get("priority", "medium"), ts, ds))

def cmd_stats(args):
    tasks = load_tasks()
    oc = sum(1 for t in tasks if not t["done"])
    dc = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: {}".format(oc))
    print("done: {}".format(dc))
    print("total: {}".format(total))

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "done": cmd_done,
        "delete": cmd_delete,
        "edit": cmd_edit,
        "search": cmd_search,
        "export": cmd_export,
        "stats": cmd_stats,
    }
    if command == "undo":
        undo()
    elif command in commands:
        commands[command](args)
    else:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
