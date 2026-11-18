#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
UNDO_FILE = "tasks_undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return {"history": [], "next_id": 1}
    with open(UNDO_FILE, "r") as f:
        return json.load(f)


def save_undo(data):
    with open(UNDO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_task(task):
    done_mark = "x" if task["done"] else " "
    line = f"{task['id']} [{done_mark}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    for tag in tags:
        line += f" #{tag}"
    due = task.get("due")
    if due:
        line += f" due:{due}"
    return line


def parse_args(args):
    """Parse command arguments into a dict of options and positional args."""
    result = {"positional": [], "options": {}}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if "=" in key:
                k, v = key.split("=", 1)
                if k not in result["options"]:
                    result["options"][k] = []
                result["options"][k].append(v)
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                if key not in result["options"]:
                    result["options"][key] = []
                result["options"][key].append(args[i + 1])
                i += 1
            else:
                if key not in result["options"]:
                    result["options"][key] = True
        else:
            result["positional"].append(arg)
        i += 1
    return result


def cmd_add(tasks, undo_data, args):
    parsed = parse_args(args)
    if not parsed["positional"]:
        print("Error: add requires a title", file=sys.stderr)
        sys.exit(1)

    title_parts = parsed["positional"]
    title = " ".join(title_parts)

    priority = "medium"
    if "priority" in parsed["options"]:
        p = parsed["options"]["priority"][0]
        if p not in ("high", "medium", "low"):
            print(f"Invalid priority: {p}", file=sys.stderr)
            sys.exit(1)
        priority = p

    tags = []
    if "tag" in parsed["options"]:
        tags = list(parsed["options"]["tag"])

    due = None
    if "due" in parsed["options"]:
        due_str = parsed["options"]["due"][0]
        try:
            datetime.strptime(due_str, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {due_str}", file=sys.stderr)
            sys.exit(1)
        due = due_str

    nid = undo_data["next_id"]
    undo_data["next_id"] = nid + 1

    # Record state before mutation
    undo_data["history"].append({
        "tasks": tasks[:],
        "next_id": undo_data["next_id"],
    })
    save_undo(undo_data)

    task = {
        "id": nid,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added {nid}")


def cmd_list(tasks, args):
    parsed = parse_args(args)

    sort_by = parsed["options"].get("sort", [None])[0]
    filter_tag = parsed["options"].get("tag", [None])[0]
    overdue = "overdue" in parsed["options"]
    today_arg = None
    if "today" in parsed["options"]:
        today_arg = parsed["options"]["today"][0]

    if today_arg:
        try:
            today = datetime.strptime(today_arg, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date: {today_arg}", file=sys.stderr)
            sys.exit(1)
    else:
        today = date.today()

    filtered = []
    for t in tasks:
        if filter_tag and filter_tag not in t.get("tags", []):
            continue
        if overdue:
            if t["done"]:
                continue
            if not t.get("due"):
                continue
            if t["due"] >= today.isoformat():
                continue
        filtered.append(t)

    if sort_by == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        filtered.sort(key=lambda t: t["id"])

    if not filtered:
        print("No tasks")
        return

    for t in filtered:
        print(format_task(t))


def cmd_done(tasks, undo_data, args):
    parsed = parse_args(args)
    if not parsed["positional"]:
        print("Error: done requires an id", file=sys.stderr)
        sys.exit(1)

    try:
        tid = int(parsed["positional"][0])
    except ValueError:
        print(f"Error: invalid id", file=sys.stderr)
        sys.exit(1)

    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break

    if not found:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Record state before mutation
    undo_data["history"].append({
        "tasks": tasks[:],
        "next_id": undo_data["next_id"],
    })
    save_undo(undo_data)

    found["done"] = True
    save_tasks(tasks)
    print(f"Done {tid}")


def cmd_delete(tasks, undo_data, args):
    parsed = parse_args(args)
    if not parsed["positional"]:
        print("Error: delete requires an id", file=sys.stderr)
        sys.exit(1)

    try:
        tid = int(parsed["positional"][0])
    except ValueError:
        print(f"Error: invalid id", file=sys.stderr)
        sys.exit(1)

    found = None
    idx = None
    for i, t in enumerate(tasks):
        if t["id"] == tid:
            found = t
            idx = i
            break

    if not found:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Record state before mutation
    undo_data["history"].append({
        "tasks": tasks[:],
        "next_id": undo_data["next_id"],
    })
    save_undo(undo_data)

    del tasks[idx]
    save_tasks(tasks)
    print(f"Deleted {tid}")


def cmd_edit(tasks, undo_data, args):
    parsed = parse_args(args)
    if not parsed["positional"]:
        print("Error: edit requires an id", file=sys.stderr)
        sys.exit(1)

    try:
        tid = int(parsed["positional"][0])
    except ValueError:
        print(f"Error: invalid id", file=sys.stderr)
        sys.exit(1)

    if "title" not in parsed["options"]:
        print("Error: edit requires --title", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(parsed["options"]["title"])

    found = None
    for t in tasks:
        if t["id"] == tid:
            found = t
            break

    if not found:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)

    # Record state before mutation
    undo_data["history"].append({
        "tasks": tasks[:],
        "next_id": undo_data["next_id"],
    })
    save_undo(undo_data)

    found["title"] = new_title
    save_tasks(tasks)
    print(f"Edited {tid}")


def cmd_search(tasks, args):
    parsed = parse_args(args)
    if not parsed["positional"]:
        print("Error: search requires text", file=sys.stderr)
        sys.exit(1)

    text = " ".join(parsed["positional"]).lower()

    matches = [t for t in tasks if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(format_task(t))


def cmd_export(tasks, args):
    parsed = parse_args(args)
    fmt = parsed["options"].get("format", ["json"])[0]

    tasks_sorted = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        export_data = []
        for t in tasks_sorted:
            export_data.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(export_data, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks_sorted:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")


def cmd_stats(tasks, args):
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(tasks, undo_data, args):
    history = undo_data.get("history", [])
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)

    previous_state = history.pop()
    undo_data["next_id"] = previous_state["next_id"]
    undo_data["history"] = history
    save_tasks(previous_state["tasks"])
    save_undo(undo_data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    tasks = load_tasks()
    undo_data = load_undo()

    if command == "add":
        cmd_add(tasks, undo_data, args)
    elif command == "list":
        cmd_list(tasks, args)
    elif command == "done":
        cmd_done(tasks, undo_data, args)
    elif command == "delete":
        cmd_delete(tasks, undo_data, args)
    elif command == "edit":
        cmd_edit(tasks, undo_data, args)
    elif command == "search":
        cmd_search(tasks, args)
    elif command == "export":
        cmd_export(tasks, args)
    elif command == "stats":
        cmd_stats(tasks, args)
    elif command == "undo":
        cmd_undo(tasks, undo_data, args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
