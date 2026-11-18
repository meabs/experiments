#!/usr/bin/env python3
import sys
import json
import os
import copy
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "max_id": 0, "history": []}
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        for k in ("tasks", "next_id", "max_id", "history"):
            if k not in data:
                data[k] = [] if k == "history" else (0 if k == "max_id" else 1)
        return data
    except Exception:
        print("Error reading data file", file=sys.stderr)
        sys.exit(1)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def push_history(data):
    data["history"].append({
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
        "max_id": data["max_id"],
    })


def undo(data, args=None):
    if not data.get("history"):
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = data["history"].pop()
    data["tasks"] = state["tasks"]
    data["next_id"] = state["next_id"]
    data["max_id"] = state["max_id"]
    save_data(data)
    print("Undone")


def find_task(data, tid):
    for t in data["tasks"]:
        if t["id"] == tid:
            return t
    return None


def fmt(task):
    s = "x" if task["done"] else " "
    line = "{} [{}] {}".format(task["id"], s, task["title"])
    p = task.get("priority", "medium")
    if p == "high":
        line += " (high)"
    elif p == "low":
        line += " (low)"
    tg = task.get("tags", [])
    if tg:
        line += " " + " ".join("#" + t for t in tg)
    d = task.get("due")
    if d:
        line += " due:" + d
    return line


def add_task(data, args):
    if not args:
        print("Usage: add TITLE [--priority high|medium|low] [--tag T] [--due D]", file=sys.stderr)
        sys.exit(1)
    priority = "medium"
    tags = []
    due = None
    title_parts = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--priority":
            if i + 1 >= len(args):
                print("--priority needs value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: " + priority, file=sys.stderr)
                sys.exit(1)
            i += 2
        elif a == "--tag":
            if i + 1 >= len(args):
                print("--tag needs value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif a == "--due":
            if i + 1 >= len(args):
                print("--due needs value", file=sys.stderr)
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
            title_parts.append(a)
            i += 1
    if not title_parts:
        print("add requires TITLE", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    tid = data["next_id"]
    task = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    push_history(data)
    data["tasks"].append(task)
    data["next_id"] = tid + 1
    if tid > data["max_id"]:
        data["max_id"] = tid
    save_data(data)
    print("Added " + str(tid))


def list_tasks(data, args):
    sort_mode = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--sort":
            if i + 1 >= len(args):
                print("--sort needs value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif a == "--tag":
            if i + 1 >= len(args):
                print("--tag needs value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif a == "--overdue":
            overdue = True
            i += 1
        elif a == "--today":
            if i + 1 >= len(args):
                print("--today needs value", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date: " + today_str, file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    tasks = list(data["tasks"])

    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if overdue:
        today = today_str if today_str else date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]

    if sort_mode == "priority":
        po = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(fmt(t))


def done_task(data, args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid ID: " + args[0], file=sys.stderr)
        sys.exit(1)
    task = find_task(data, tid)
    if task is None:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    task["done"] = True
    save_data(data)
    print("Done " + str(tid))


def delete_task(data, args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid ID: " + args[0], file=sys.stderr)
        sys.exit(1)
    task = find_task(data, tid)
    if task is None:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    push_history(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    save_data(data)
    print("Deleted " + str(tid))


def edit_task(data, args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid ID: " + args[0], file=sys.stderr)
        sys.exit(1)
    task = find_task(data, tid)
    if task is None:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    new_title_parts = []
    i = 1
    got_title = False
    while i < len(args):
        a = args[i]
        if a == "--title":
            got_title = True
            i += 1
            while i < len(args):
                narg = args[i]
                if narg.startswith("--"):
                    break
                new_title_parts.append(narg)
                i += 1
        else:
            i += 1
    if not got_title or not new_title_parts:
        print("edit requires --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(new_title_parts)
    push_history(data)
    task["title"] = new_title
    save_data(data)
    print("Edited " + str(tid))


def search_tasks(data, args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    results = [t for t in data["tasks"] if query in t["title"].lower()]
    results.sort(key=lambda t: t["id"])
    if not results:
        print("No matches")
        return
    for t in results:
        print(fmt(t))


def export_tasks(data, args):
    fmt_type = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--format":
            if i + 1 >= len(args):
                print("--format needs value", file=sys.stderr)
                sys.exit(1)
            fmt_type = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt_type:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt_type == "json":
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
    elif fmt_type == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str
            ))
    else:
        print("Invalid format: " + fmt_type, file=sys.stderr)
        sys.exit(1)


def stats(data, args):
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total_count = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


COMMANDS = {
    "add": add_task,
    "list": list_tasks,
    "done": done_task,
    "delete": delete_task,
    "edit": edit_task,
    "search": search_tasks,
    "export": export_tasks,
    "stats": stats,
    "undo": undo,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command not in COMMANDS:
        print("Unknown command: " + command, file=sys.stderr)
        sys.exit(1)

    data = load_data()
    COMMANDS[command](data, args)


if __name__ == "__main__":
    main()
