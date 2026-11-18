#!/usr/bin/env python3
"""A command-line task manager."""

import copy
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks.undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    tasks = {int(k): v for k, v in data["tasks"].items()}
    return tasks, data["next_id"]


def save_tasks(tasks, next_id):
    data = {"tasks": tasks, "next_id": next_id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f, indent=2)


def push_undo(tasks, next_id):
    history = load_undo()
    history.append({"tasks": copy.deepcopy(tasks), "next_id": next_id})
    if len(history) > 100:
        history = history[-100:]
    save_undo(history)


def pop_undo():
    history = load_undo()
    if not history:
        return None
    state = history.pop()
    save_undo(history)
    return state["tasks"], state["next_id"]


def format_task_line(task):
    status = "x" if task["done"] else " "
    line = f'{task["id"]} [{status}] {task["title"]}'
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join(f"#{t}" for t in tags)
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def parse_argv():
    raw = sys.argv[1:]
    if not raw:
        return None, [], {}, set()
    command = raw[0]
    positional = []
    flags = {}
    is_set = set()
    j = 1
    while j < len(raw):
        arg = raw[j]
        if arg.startswith("--"):
            flag_name = arg[2:]
            if flag_name == "tag" and j + 1 < len(raw):
                if "tag" not in flags:
                    flags["tag"] = []
                flags["tag"].append(raw[j + 1])
                is_set.add("tag")
                j += 2
            elif flag_name == "today" and j + 1 < len(raw):
                flags["today"] = raw[j + 1]
                is_set.add("today")
                j += 2
            elif flag_name == "priority" and j + 1 < len(raw):
                flags["priority"] = raw[j + 1]
                is_set.add("priority")
                j += 2
            elif flag_name == "due" and j + 1 < len(raw):
                flags["due"] = raw[j + 1]
                is_set.add("due")
                j += 2
            elif flag_name == "title" and j + 1 < len(raw):
                flags["title"] = " ".join(raw[j + 1:])
                is_set.add("title")
                break
            elif flag_name == "format" and j + 1 < len(raw):
                flags["format"] = raw[j + 1]
                is_set.add("format")
                j += 2
            elif flag_name == "sort" and j + 1 < len(raw):
                flags["sort"] = raw[j + 1]
                is_set.add("sort")
                j += 2
            elif flag_name == "overdue":
                is_set.add("overdue")
                j += 1
            else:
                is_set.add(flag_name)
                j += 1
        else:
            positional.append(arg)
            j += 1
    return command, positional, flags, is_set


def cmd_add(positional, flags, is_set):
    if not positional:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(positional)
    priority = "medium"
    if "priority" in flags:
        priority = flags["priority"]
        if priority not in ("high", "medium", "low"):
            print(f"Invalid priority: {priority}", file=sys.stderr)
            sys.exit(1)
    tags = flags.get("tag", [])
    due = None
    if "due" in flags:
        due_str = flags["due"]
        try:
            datetime.strptime(due_str, "%Y-%m-%d")
            due = due_str
        except ValueError:
            print(f"Invalid date: {due_str}", file=sys.stderr)
            sys.exit(1)
    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)
    task_id = next_id
    tasks[task_id] = {
        "id": task_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    save_tasks(tasks, next_id + 1)
    print(f"Added {task_id}")


def cmd_list(positional, flags, is_set):
    tasks, _ = load_tasks()
    if not tasks:
        print("No tasks")
        return
    result = list(tasks.values())
    if "tag" in is_set:
        filter_tag = flags["tag"][0]
        result = [t for t in result if filter_tag in t.get("tags", [])]
    if "overdue" in is_set:
        today_str = flags.get("today", date.today().isoformat())
        result = [t for t in result if not t["done"] and t.get("due") and t["due"] < today_str]
    if "sort" in is_set and flags.get("sort") == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        result.sort(key=lambda t: t["id"])
    if not result:
        print("No tasks")
        return
    for task in result:
        print(format_task_line(task))


def cmd_done(positional, flags, is_set):
    if not positional:
        print("Error: done requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Error: ID must be an integer", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def cmd_delete(positional, flags, is_set):
    if not positional:
        print("Error: delete requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Error: ID must be an integer", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def cmd_edit(positional, flags, is_set):
    if not positional:
        print("Error: edit requires an ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(positional[0])
    except ValueError:
        print("Error: ID must be an integer", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    if "title" not in is_set:
        print("Error: edit requires --title", file=sys.stderr)
        sys.exit(1)
    new_title = flags["title"]
    push_undo(tasks, next_id)
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def cmd_search(positional, flags, is_set):
    if not positional:
        print("Error: search requires TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(positional).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks.values() if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def cmd_export(positional, flags, is_set):
    if "format" not in is_set:
        print("Error: export requires --format", file=sys.stderr)
        sys.exit(1)
    fmt = flags["format"]
    tasks, _ = load_tasks()
    result = sorted(tasks.values(), key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in result:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in result:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            done_str = "true" if t["done"] else "false"
            priority = t.get("priority", "medium")
            line = f'{t["id"]},{t["title"]},{done_str},{priority},{tags_str},{due_str}'
            print(line)
    else:
        print(f"Error: Unknown format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(positional, flags, is_set):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total_count = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def cmd_undo(positional, flags, is_set):
    state = pop_undo()
    if state is None:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = state
    save_tasks(tasks, next_id)
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
    command, positional, flags, is_set = parse_argv()
    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
    COMMANDS[command](positional, flags, is_set)


if __name__ == "__main__":
    main()
