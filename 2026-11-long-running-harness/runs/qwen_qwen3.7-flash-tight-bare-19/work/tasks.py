#!/usr/bin/env python3
"""A command-line task manager."""
import copy
import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_data(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(tasks, next_id):
    history = load_history()
    history.append({"tasks": copy.deepcopy(tasks), "next_id": next_id})
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        return None
    state = history.pop()
    save_history(history)
    return state["tasks"], state["next_id"]


def fmt(task):
    st = "x" if task["done"] else " "
    s = "%d [%s] %s" % (task["id"], st, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        s += " (high)"
    elif priority == "low":
        s += " (low)"
    for tag in task.get("tags", []):
        s += " #%s" % tag
    if task.get("due"):
        s += " due:%s" % task["due"]
    return s


def parse_args(args):
    result = {"_args": []}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if key in ("tag", "format", "sort", "today", "title", "priority", "due"):
                if i + 1 >= len(args):
                    print("Missing value for --%s" % key, file=sys.stderr)
                    sys.exit(1)
                val = args[i + 1]
                if key not in result:
                    result[key] = []
                if isinstance(result[key], list):
                    result[key].append(val)
                else:
                    result[key] = [result[key], val]
                i += 2
            else:
                result[key] = True
                i += 1
        else:
            result["_args"].append(arg)
            i += 1
    return result


def cmd_add(args):
    parsed = parse_args(args)
    title_parts = parsed["_args"]
    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)

    priority_list = parsed.get("priority", ["medium"])
    if len(priority_list) > 1:
        print("Duplicate --priority", file=sys.stderr)
        sys.exit(1)
    priority = priority_list[0]
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: %s" % priority, file=sys.stderr)
        sys.exit(1)

    tags = parsed.get("tag", [])

    due = None
    if "due" in parsed:
        due_vals = parsed["due"]
        if len(due_vals) > 1:
            print("Duplicate --due", file=sys.stderr)
            sys.exit(1)
        due_val = due_vals[0]
        try:
            datetime.strptime(due_val, "%Y-%m-%d")
        except ValueError:
            print("Invalid date: %s" % due_val, file=sys.stderr)
            sys.exit(1)
        due = due_val

    tasks, next_id = load_data()
    push_history(tasks, next_id)
    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    next_id += 1
    save_data(tasks, next_id)
    print("Added %d" % task["id"])


def cmd_list(args):
    parsed = parse_args(args)
    all_tasks, _ = load_data()
    filtered = list(all_tasks)

    if "tag" in parsed:
        tag_filter = parsed["tag"][0]
        filtered = [t for t in filtered if tag_filter in t.get("tags", [])]

    if "overdue" in parsed:
        today_str = parsed.get("today", [None])
        if today_str[0] is None:
            today_str = [date.today().strftime("%Y-%m-%d")]
        today = today_str[0]
        filtered = [t for t in filtered if not t["done"] and t.get("due") and t["due"] < today]

    if not filtered:
        print("No tasks")
        return

    if parsed.get("sort") == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    for task in filtered:
        print(fmt(task))


def cmd_done(args):
    parsed = parse_args(args)
    if not parsed["_args"]:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(parsed["_args"][0])
    except ValueError:
        print("Invalid ID: %s" % parsed["_args"][0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_data()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            push_history(tasks, next_id)
            task["done"] = True
            save_data(tasks, next_id)
            print("Done %d" % task_id)
            break
    if not found:
        print("No such task: %d" % task_id, file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    parsed = parse_args(args)
    if not parsed["_args"]:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(parsed["_args"][0])
    except ValueError:
        print("Invalid ID: %s" % parsed["_args"][0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_data()
    found = False
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            found = True
            push_history(tasks, next_id)
            tasks.pop(i)
            save_data(tasks, next_id)
            print("Deleted %d" % task_id)
            break
    if not found:
        print("No such task: %d" % task_id, file=sys.stderr)
        sys.exit(1)


def cmd_edit(args):
    parsed = parse_args(args)
    if not parsed["_args"]:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(parsed["_args"][0])
    except ValueError:
        print("Invalid ID: %s" % parsed["_args"][0], file=sys.stderr)
        sys.exit(1)
    if "title" not in parsed:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    new_title = " ".join(parsed["title"])
    tasks, next_id = load_data()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            push_history(tasks, next_id)
            task["title"] = new_title
            save_data(tasks, next_id)
            print("Edited %d" % task_id)
            break
    if not found:
        print("No such task: %d" % task_id, file=sys.stderr)
        sys.exit(1)


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(args).lower()
    tasks, _ = load_data()
    matches = [t for t in tasks if text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    matches.sort(key=lambda t: t["id"])
    for task in matches:
        print(fmt(task))


def cmd_export(args):
    parsed = parse_args(args)
    if "format" not in parsed:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    fmt_type = parsed["format"][0]
    tasks, _ = load_data()
    tasks.sort(key=lambda t: t["id"])

    if fmt_type == "json":
        output = []
        for task in tasks:
            output.append({
                "id": task["id"],
                "title": task["title"],
                "done": task["done"],
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
                "due": task.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt_type == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "title", "done", "priority", "tags", "due"])
        for task in tasks:
            writer.writerow([
                task["id"],
                task["title"],
                "true" if task["done"] else "false",
                task.get("priority", "medium"),
                ";".join(task.get("tags", [])),
                task.get("due", ""),
            ])
        print(buf.getvalue(), end="")
    else:
        print("Invalid format: %s" % fmt_type, file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, _ = load_data()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print("open: %d" % open_count)
    print("done: %d" % done_count)
    print("total: %d" % total)


def cmd_undo(args):
    state = pop_history()
    if state is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = state
    save_data(tasks, next_id)
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
        print("Unknown command: %s" % command, file=sys.stderr)
        sys.exit(1)
    COMMANDS[command](sys.argv[2:])


if __name__ == "__main__":
    main()
