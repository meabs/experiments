#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def snapshot(data):
    return {
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    }


def push_undo(data, snap):
    data["history"].append(snap)


def pop_undo(data):
    if not data["history"]:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = data["history"].pop()
    data["tasks"] = prev["tasks"]
    data["next_id"] = prev["next_id"]


def format_task_line(task):
    check = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {check} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        tag_str = " ".join(f"#{t}" for t in tags)
        line += f" {tag_str}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_args(args):
    cmd = args[0]
    rest = args[1:]
    result = {"cmd": cmd, "positional": [], "flags": {}, "flag_values": {}}
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg.startswith("--"):
            flag_name = arg[2:]
            if flag_name in ("priority", "tag", "due", "sort", "format", "today"):
                if i + 1 >= len(rest):
                    print(f"Missing value for --{flag_name}", file=sys.stderr)
                    sys.exit(1)
                val = rest[i + 1]
                if flag_name not in result["flag_values"]:
                    result["flag_values"][flag_name] = []
                result["flag_values"][flag_name].append(val)
                i += 2
            elif flag_name == "title":
                title_parts = []
                j = i + 1
                while j < len(rest) and not rest[j].startswith("--"):
                    title_parts.append(rest[j])
                    j += 1
                if not title_parts:
                    print(f"Missing value for --title", file=sys.stderr)
                    sys.exit(1)
                result["flag_values"]["title"] = [" ".join(title_parts)]
                i = j
            else:
                result["flags"][flag_name] = True
                i += 1
        else:
            result["positional"].append(arg)
            i += 1
    return result


def get_flag_val(result, key, default=None):
    vals = result["flag_values"].get(key, [])
    if vals:
        return vals[0]
    return default


def get_all_flag_vals(result, key):
    return result["flag_values"].get(key, [])


def do_add(data, parsed):
    if not parsed["positional"]:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title_parts = []
    for part in parsed["positional"]:
        if part.startswith("--"):
            break
        title_parts.append(part)
    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    priority = get_flag_val(parsed, "priority", "medium")
    if priority not in ("high", "medium", "low"):
        print(f"Invalid priority: {priority}", file=sys.stderr)
        sys.exit(1)
    tags = get_all_flag_vals(parsed, "tag")
    due = get_flag_val(parsed, "due")
    if due is not None:
        if not validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)
    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    snap = snapshot(data)
    push_undo(data, snap)
    save_data(data)
    print(f"Added {task['id']}")


def do_list(data, parsed):
    sort_by = get_flag_val(parsed, "sort")
    tag_filter = get_flag_val(parsed, "tag")
    overdue = parsed["flags"].get("overdue", False)
    today_str = get_flag_val(parsed, "today")
    if today_str is not None:
        if not validate_date(today_str):
            print(f"Invalid date: {today_str}", file=sys.stderr)
            sys.exit(1)
        today_dt = date.fromisoformat(today_str)
    else:
        today_dt = date.today()
    tasks = list(data["tasks"])
    if tag_filter is not None:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_task_line(task))


def do_done(data, parsed):
    if not parsed["positional"]:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(parsed["positional"][0])
    except ValueError:
        print(f"No such task: {parsed['positional'][0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["done"] = True
    snap = snapshot(data)
    push_undo(data, snap)
    save_data(data)
    print(f"Done {task_id}")


def do_delete(data, parsed):
    if not parsed["positional"]:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(parsed["positional"][0])
    except ValueError:
        print(f"No such task: {parsed['positional'][0]}", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    data["tasks"].remove(task)
    snap = snapshot(data)
    push_undo(data, snap)
    save_data(data)
    print(f"Deleted {task_id}")


def do_edit(data, parsed):
    if not parsed["positional"]:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(parsed["positional"][0])
    except ValueError:
        print(f"No such task: {parsed['positional'][0]}", file=sys.stderr)
        sys.exit(1)
    new_title = get_flag_val(parsed, "title")
    if new_title is None:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        print(f"No such task: {task_id}", file=sys.stderr)
        sys.exit(1)
    task["title"] = new_title
    snap = snapshot(data)
    push_undo(data, snap)
    save_data(data)
    print(f"Edited {task_id}")


def do_search(data, parsed):
    if not parsed["positional"]:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    text = " ".join(parsed["positional"]).lower()
    matches = []
    for t in data["tasks"]:
        if text in t["title"].lower():
            matches.append(t)
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task_line(task))


def do_export(data, parsed):
    fmt = get_flag_val(parsed, "format")
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due", None),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            done_str = "true" if t["done"] else "false"
            priority_str = t.get("priority", "medium")
            print(f"{t['id']},{t['title']},{done_str},{priority_str},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def do_stats(data, parsed):
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total_count = len(data["tasks"])
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total_count}")


def do_undo(data, parsed):
    pop_undo(data)
    save_data(data)
    print("Undone")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    data = load_data()
    parsed = parse_args(sys.argv[1:])
    cmd = parsed["cmd"]
    commands = {
        "add": do_add,
        "list": do_list,
        "done": do_done,
        "delete": do_delete,
        "edit": do_edit,
        "search": do_search,
        "export": do_export,
        "stats": do_stats,
        "undo": do_undo,
    }
    handler = commands.get(cmd)
    if handler is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    handler(data, parsed)


if __name__ == "__main__":
    main()
