#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def record_undo(data):
    history = load_history()
    history.append(json.dumps(data))
    if len(history) > 1000:
        history = history[-1000:]
    save_history(history)


def cmd_undo(data):
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    previous_state = json.loads(history.pop())
    save_history(history)
    save_data(previous_state)
    print("Undone")


def format_task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = '{} {} {}'.format(task["id"], status, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        tags_str = " ".join("#" + t for t in task["tags"])
        line += " " + tags_str
    if task.get("due"):
        line += ' due:' + task["due"]
    return line


def parse_args(args):
    result = {}
    i = 0
    positional = []
    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            result.setdefault("tags", []).append(args[i + 1])
            i += 2
        elif args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            result["priority"] = args[i + 1]
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            result["due"] = args[i + 1]
            i += 2
        elif args[i] == "--title":
            if i + 1 >= len(args):
                print("--title requires a value", file=sys.stderr)
                sys.exit(1)
            i += 1
            parts = []
            while i < len(args) and not args[i].startswith("--"):
                parts.append(args[i])
                i += 1
            result["title"] = " ".join(parts)
        elif args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                result[key] = args[i + 1]
                i += 2
            else:
                result[key] = True
                i += 1
        else:
            positional.append(args[i])
            i += 1
    return positional, result


def cmd_add(args):
    positional, kw = parse_args(args)
    if not positional:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)

    title = " ".join(positional)
    priority = kw.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)

    due = None
    if "due" in kw:
        try:
            date.fromisoformat(kw["due"])
            due = kw["due"]
        except ValueError:
            print("Invalid date: {}".format(kw["due"]), file=sys.stderr)
            sys.exit(1)

    data = load_data()
    record_undo(data)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": kw.get("tags", []),
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print("Added {}".format(task["id"]))


def cmd_list(args):
    data = load_data()
    if not data["tasks"]:
        print("No tasks")
        return

    _, kw = parse_args(args)
    tasks = list(data["tasks"])

    if "tag" in kw:
        tag_filter = kw["tag"]
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if kw.get("overdue"):
        today_str = kw.get("today", date.today().isoformat())
        try:
            today = date.fromisoformat(today_str)
        except ValueError:
            print("Invalid date: {}".format(today_str), file=sys.stderr)
            sys.exit(1)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and date.fromisoformat(t["due"]) < today]

    if kw.get("sort") == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    for task in tasks:
        print(format_task_line(task))


def cmd_done(args):
    positional, kw = parse_args(args)
    if not positional:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)

    data = load_data()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            record_undo(data)
            save_data(data)
            print("Done {}".format(task_id))
            return
    print("No such task: {}".format(task_id), file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    positional, kw = parse_args(args)
    if not positional:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)

    data = load_data()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            data["tasks"].pop(i)
            record_undo(data)
            save_data(data)
            print("Deleted {}".format(task_id))
            return
    print("No such task: {}".format(task_id), file=sys.stderr)
    sys.exit(1)


def cmd_edit(args):
    positional, kw = parse_args(args)
    if not positional:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Invalid id: {}".format(positional[0]), file=sys.stderr)
        sys.exit(1)

    if "title" not in kw:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    for task in data["tasks"]:
        if task["id"] == task_id:
            record_undo(data)
            task["title"] = kw["title"]
            save_data(data)
            print("Edited {}".format(task_id))
            return
    print("No such task: {}".format(task_id), file=sys.stderr)
    sys.exit(1)


def cmd_search(args):
    positional, kw = parse_args(args)
    if not positional:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(positional).lower()

    data = load_data()
    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(format_task_line(task))


def cmd_export(args):
    _, kw = parse_args(args)
    fmt = kw.get("format")
    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
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
        print("Invalid format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    data = load_data()
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": lambda args: cmd_undo(load_data()),
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    if command not in COMMANDS:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
