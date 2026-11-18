#!/usr/bin/env python3
"""Command-line task manager."""

import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load_data():
    """Load tasks and undo history from data file."""
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save tasks and undo history to data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def error(msg):
    """Print error message to stderr and exit with code 1."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def task_line(task):
    """Format a task as a display line."""
    done_marker = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], done_marker, task["title"])
    # Priority suffix (only high/low shown; medium is implicit)
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    # Tags suffix
    for tag in task.get("tags", []):
        line += " #{}".format(tag)
    # Due date suffix
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def parse_args(argv):
    """Parse command-line arguments into a structured dict.

    Handles repeatable flags by collecting all values per flag name.
    """
    if not argv:
        return {"cmd": None, "positional": [], "flags": set(), "flag_values": {}}

    cmd = argv[0]
    rest = argv[1:]

    positional = []
    flags = set()
    # Use a list of lists to accumulate values for repeatable flags
    flag_value_lists = {}

    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg.startswith("--"):
            flag_name = arg[2:]
            flags.add(flag_name)
            vals = []
            i += 1
            while i < len(rest) and not rest[i].startswith("--"):
                vals.append(rest[i])
                i += 1
            if vals:
                if flag_name not in flag_value_lists:
                    flag_value_lists[flag_name] = vals
                else:
                    flag_value_lists[flag_name].extend(vals)
            else:
                flag_value_lists.setdefault(flag_name, [])
        else:
            positional.append(arg)
            i += 1

    return {
        "cmd": cmd,
        "positional": positional,
        "flags": flags,
        "flag_values": flag_value_lists,
    }


def cmd_add(data, parsed):
    """Add a new task."""
    positional = parsed["positional"]
    title = " ".join(positional)
    if not title:
        error("No title provided")

    priority = parsed["flag_values"].get("priority", ["medium"])[0]
    if priority not in ("high", "medium", "low"):
        error("Invalid priority: {}".format(priority))

    tags = parsed["flag_values"].get("tag", [])

    due = None
    if "due" in parsed["flags"]:
        due_str = parsed["flag_values"]["due"][0]
        try:
            datetime.strptime(due_str, "%Y-%m-%d")
            due = due_str
        except ValueError:
            error("Invalid date: {}".format(due_str))

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }

    # Save snapshot for undo before mutation
    data["undo_stack"].append(json.dumps({
        "next_id": data["next_id"],
        "tasks": data["tasks"],
    }))

    data["tasks"].append(task)
    data["next_id"] += 1
    save_data(data)
    print("Added {}".format(task["id"]))


def cmd_list(data, parsed):
    """List tasks."""
    sort_by = parsed["flag_values"].get("sort", [""])[0]
    filter_tag = parsed["flag_values"].get("tag", [None])[0]
    overdue = "overdue" in parsed["flags"]
    today_str = parsed["flag_values"].get("today", [None])[0]

    tasks = list(data["tasks"])

    # Filter by tag
    if filter_tag is not None:
        tasks = [t for t in tasks if filter_tag in t["tags"]]

    # Filter overdue
    if overdue:
        if today_str:
            try:
                today = datetime.strptime(today_str, "%Y-%m-%d").date()
            except ValueError:
                error("Invalid date: {}".format(today_str))
        else:
            today = date.today()
        tasks = [
            t for t in tasks
            if not t["done"] and t.get("due") and t["due"] < today.strftime("%Y-%m-%d")
        ]

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (priority_order.get(t["priority"], 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for task in tasks:
        print(task_line(task))


def cmd_done(data, parsed):
    """Mark a task as done."""
    if not parsed["positional"]:
        error("No task ID provided")
    try:
        task_id = int(parsed["positional"][0])
    except ValueError:
        error("Invalid task ID: {}".format(parsed["positional"][0]))

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error("No such task: {}".format(task_id))

    # Save snapshot for undo
    data["undo_stack"].append(json.dumps({
        "next_id": data["next_id"],
        "tasks": data["tasks"],
    }))

    task["done"] = True
    save_data(data)
    print("Done {}".format(task_id))


def cmd_delete(data, parsed):
    """Delete a task."""
    if not parsed["positional"]:
        error("No task ID provided")
    try:
        task_id = int(parsed["positional"][0])
    except ValueError:
        error("Invalid task ID: {}".format(parsed["positional"][0]))

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error("No such task: {}".format(task_id))

    # Save snapshot for undo
    data["undo_stack"].append(json.dumps({
        "next_id": data["next_id"],
        "tasks": data["tasks"],
    }))

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    print("Deleted {}".format(task_id))


def cmd_edit(data, parsed):
    """Edit a task's title."""
    if not parsed["positional"]:
        error("No task ID provided")
    try:
        task_id = int(parsed["positional"][0])
    except ValueError:
        error("Invalid task ID: {}".format(parsed["positional"][0]))

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        error("No such task: {}".format(task_id))

    if "title" not in parsed["flags"]:
        error("No title provided")

    new_title = " ".join(parsed["flag_values"]["title"])

    # Save snapshot for undo
    data["undo_stack"].append(json.dumps({
        "next_id": data["next_id"],
        "tasks": data["tasks"],
    }))

    task["title"] = new_title
    save_data(data)
    print("Edited {}".format(task_id))


def cmd_search(data, parsed):
    """Search tasks by title."""
    if not parsed["positional"]:
        error("No search text provided")

    text = " ".join(parsed["positional"]).lower()

    matches = [t for t in data["tasks"] if text in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for task in matches:
        print(task_line(task))


def cmd_export(data, parsed):
    """Export tasks in JSON or CSV format."""
    fmt = parsed["flag_values"].get("format", [""])[0]
    if fmt not in ("json", "csv"):
        error("Invalid format: {}".format(fmt))

    tasks = sorted(data["tasks"], key=lambda t: t["id"])

    if fmt == "json":
        export_tasks = []
        for t in tasks:
            export_tasks.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t["priority"],
                "tags": t["tags"],
                "due": t["due"],
            })
        print(json.dumps(export_tasks))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t["tags"])
            due_str = t["due"] if t["due"] else ""
            print("{},{},{},{},{},{}".format(
                t["id"],
                t["title"],
                str(t["done"]).lower(),
                t["priority"],
                tags_str,
                due_str,
            ))


def cmd_stats(data, parsed):
    """Show task statistics."""
    open_count = sum(1 for t in data["tasks"] if not t["done"])
    done_count = sum(1 for t in data["tasks"] if t["done"])
    total_count = len(data["tasks"])
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))


def cmd_undo(data, parsed):
    """Undo the most recent mutating command."""
    if not data["undo_stack"]:
        error("Nothing to undo")

    prev_state = json.loads(data["undo_stack"].pop())
    data["next_id"] = prev_state["next_id"]
    data["tasks"] = prev_state["tasks"]
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
    argv = sys.argv[1:]
    if not argv:
        error("Usage: python3 tasks.py <command> [args]")

    parsed = parse_args(argv)
    cmd = parsed["cmd"]

    if cmd not in COMMANDS:
        error("Unknown command: {}".format(cmd))

    data = load_data()
    COMMANDS[cmd](data, parsed)


if __name__ == "__main__":
    main()
