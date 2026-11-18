#!/usr/bin/env python3
"""Command-line task manager."""

import json, sys, os, copy
from datetime import date

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "next_id": 1, "history": []}
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        # Convert string keys back to int
        tasks = {}
        for k, v in data["tasks"].items():
            tasks[int(k)] = v
        data["tasks"] = tasks
        return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": {}, "next_id": 1, "history": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def make_task_line(task):
    tid = task["id"]
    st = "x" if task["done"] else " "
    parts = [str(tid) + " [" + st + "] " + task["title"]]
    if task["priority"] == "high":
        parts.append("(high)")
    elif task["priority"] == "low":
        parts.append("(low)")
    for tag in task["tags"]:
        parts.append("#" + tag)
    if task["due"]:
        parts.append("due:" + task["due"])
    return " ".join(parts)


def cmd_add(args, data):
    title_parts = []
    priority = "medium"
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
                print("Invalid priority: " + priority, file=sys.stderr)
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
                print("Missing due date value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                date.fromisoformat(due)
            except ValueError:
                print("Invalid date: " + due, file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    tid = data["next_id"]
    task = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags[:],
        "due": due,
    }
    data["tasks"][tid] = task
    data["next_id"] = tid + 1
    data["history"].append({
        "type": "add",
        "task_id": tid,
        "prev_next_id": tid,
    })
    save_data(data)
    print("Added " + str(tid))


def cmd_list(args, data):
    sort_priority = False
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            if args[i + 1] == "priority":
                sort_priority = True
            else:
                print("Unknown sort option: " + args[i + 1], file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing today date", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            try:
                date.fromisoformat(today_str)
            except ValueError:
                print("Invalid date: " + today_str, file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print("Unknown option: " + args[i], file=sys.stderr)
            sys.exit(1)
    if today_str is None:
        today_str = date.today().isoformat()
    today = date.fromisoformat(today_str)
    tasks = list(data["tasks"].values())
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t["tags"]]
    if overdue:
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t["due"] and t["due"] < today_str:
                filtered.append(t)
        tasks = filtered
    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (prio_order.get(t["priority"], 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(make_task_line(t))


def cmd_done(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid id: " + args[0], file=sys.stderr)
        sys.exit(1)
    if tid not in data["tasks"]:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    prev_state = copy.deepcopy(data["tasks"][tid])
    data["tasks"][tid]["done"] = True
    data["history"].append({
        "type": "done",
        "task_id": tid,
        "prev_state": prev_state,
        "prev_next_id": data["next_id"],
    })
    save_data(data)
    print("Done " + str(tid))


def cmd_delete(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid id: " + args[0], file=sys.stderr)
        sys.exit(1)
    if tid not in data["tasks"]:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    deleted_task = copy.deepcopy(data["tasks"][tid])
    del data["tasks"][tid]
    data["history"].append({
        "type": "delete",
        "task_id": tid,
        "deleted_task": deleted_task,
        "prev_next_id": data["next_id"],
    })
    save_data(data)
    print("Deleted " + str(tid))


def cmd_edit(args, data):
    if not args:
        print("Missing task id", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print("Invalid id: " + args[0], file=sys.stderr)
        sys.exit(1)
    if tid not in data["tasks"]:
        print("No such task: " + str(tid), file=sys.stderr)
        sys.exit(1)
    new_title_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing new title", file=sys.stderr)
                sys.exit(1)
            new_title_parts.append(args[i + 1])
            i += 2
        else:
            print("Unknown option: " + args[i], file=sys.stderr)
            sys.exit(1)
    if not new_title_parts:
        print("Missing new title", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(new_title_parts)
    prev_state = copy.deepcopy(data["tasks"][tid])
    data["tasks"][tid]["title"] = new_title
    data["history"].append({
        "type": "edit",
        "task_id": tid,
        "prev_state": prev_state,
        "prev_next_id": data["next_id"],
    })
    save_data(data)
    print("Edited " + str(tid))


def cmd_search(args, data):
    if not args:
        print("Missing search text", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    matches = [t for t in tasks if search_text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(make_task_line(t))


def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ("json", "csv"):
                print("Unknown format: " + fmt, file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print("Unknown option: " + args[i], file=sys.stderr)
            sys.exit(1)
    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"].values(), key=lambda t: t["id"])
    if fmt == "json":
        out = []
        for t in tasks:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(out))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print("{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t["priority"], tags_str, due_str))


def cmd_stats(args, data):
    tasks = list(data["tasks"].values())
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: " + str(open_count))
    print("done: " + str(done_count))
    print("total: " + str(total_count))


def cmd_undo(args, data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    entry = data["history"].pop()
    etype = entry["type"]
    tid = entry["task_id"]
    if etype == "add":
        if tid in data["tasks"]:
            del data["tasks"][tid]
        data["next_id"] = entry["prev_next_id"]
    elif etype == "done":
        prev = entry["prev_state"]
        data["tasks"][tid] = prev
        data["next_id"] = entry["prev_next_id"]
    elif etype == "delete":
        task = copy.deepcopy(entry["deleted_task"])
        data["tasks"][tid] = task
        data["next_id"] = entry["prev_next_id"]
    elif etype == "edit":
        prev = entry["prev_state"]
        data["tasks"][tid] = prev
        data["next_id"] = entry["prev_next_id"]
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
    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: " + command, file=sys.stderr)
        sys.exit(1)
    data = load_data()
    COMMANDS[command](sys.argv[2:], data)
    save_data(data)


if __name__ == "__main__":
    main()
