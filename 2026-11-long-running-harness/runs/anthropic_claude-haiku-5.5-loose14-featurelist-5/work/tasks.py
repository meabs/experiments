#!/usr/bin/env python3
"""Command-line task manager. Data is stored in tasks.json in the cwd."""
import datetime
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def record(state):
    """Push a snapshot of the mutable state onto the undo history."""
    state.setdefault("history", []).append({
        "next_id": state["next_id"],
        "tasks": json.loads(json.dumps(state["tasks"])),
    })


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def validate_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        fail(f"Invalid date: {value}")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        fail(f"Invalid date: {value}")
    return value


def parse_options(args, valued, flags=()):
    """Split args into positionals and a dict of option values.

    `valued` is the set of option names (e.g. '--priority') that take a value.
    Unknown options are an error.
    """
    positional = []
    options = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in valued:
            if i + 1 >= len(args):
                fail(f"Missing value for {arg}")
            options.setdefault(arg, []).append(args[i + 1])
            i += 2
        elif arg in flags:
            options.setdefault(arg, []).append(True)
            i += 1
        elif arg.startswith("--"):
            fail(f"Unknown option: {arg}")
        else:
            positional.append(arg)
            i += 1
    return positional, options


def cmd_add(args):
    positional, options = parse_options(args, {"--priority", "--tag", "--due"})
    if len(positional) != 1:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = positional[0]
    priority = options.get("--priority", ["medium"])[-1]
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    due = options.get("--due", [None])[-1]
    if due is not None:
        validate_date(due)
    state = load()
    record(state)
    task_id = state["next_id"]
    state["next_id"] = task_id + 1
    tags = options.get("--tag", [])
    state["tasks"].append({"id": task_id, "title": title, "done": False,
                           "priority": priority, "tags": tags, "due": due})
    save(state)
    print(f"Added {task_id}")


def task_priority(task):
    return task.get("priority", "medium")


def task_tags(task):
    return task.get("tags", [])


def task_due(task):
    return task.get("due")


def format_line(task):
    mark = "x" if task.get("done") else " "
    line = f"{task['id']} [{mark}] {task['title']}"
    priority = task_priority(task)
    if priority != "medium":
        line += f" ({priority})"
    for tag in task_tags(task):
        line += f" #{tag}"
    due = task_due(task)
    if due:
        line += f" due:{due}"
    return line


def cmd_list(args):
    positional, options = parse_options(args, {"--sort", "--tag", "--today"}, {"--overdue"})
    if positional:
        fail(f"Unexpected arguments: {' '.join(positional)}")
    sort = options.get("--sort", [None])[-1]
    if sort not in (None, "priority"):
        fail(f"Invalid sort: {sort}")
    tag = options.get("--tag", [None])[-1]
    today = options.get("--today", [None])[-1]
    if today is None:
        today = datetime.date.today().isoformat()
    else:
        validate_date(today)
    overdue = "--overdue" in options
    state = load()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if tag is not None:
        tasks = [t for t in tasks if tag in task_tags(t)]
    if overdue:
        tasks = [t for t in tasks if not t.get("done") and task_due(t)
                 and task_due(t) < today]
    if sort == "priority":
        tasks = sorted(tasks, key=lambda t: PRIORITY_RANK[task_priority(t)])
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(format_line(task))


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    state = load()
    for task in state["tasks"]:
        if task["id"] == task_id:
            record(state)
            task["done"] = True
            save(state)
            print(f"Done {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_delete(args):
    if len(args) != 1:
        fail("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    state = load()
    for i, task in enumerate(state["tasks"]):
        if task["id"] == task_id:
            record(state)
            del state["tasks"][i]
            save(state)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_edit(args):
    if "--title" not in args:
        fail("Usage: edit ID --title NEW TITLE")
    idx = args.index("--title")
    before, title_words = args[:idx], args[idx + 1:]
    if len(before) != 1 or not title_words:
        fail("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(before[0])
    except ValueError:
        fail(f"No such task: {before[0]}")
    title = " ".join(title_words)
    state = load()
    for task in state["tasks"]:
        if task["id"] == task_id:
            record(state)
            task["title"] = title
            save(state)
            print(f"Edited {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_search(args):
    if len(args) != 1:
        fail("Usage: search TEXT")
    needle = args[0].lower()
    state = load()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    matches = [t for t in tasks if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_line(task))


def cmd_export(args):
    positional, options = parse_options(args, {"--format"})
    if positional:
        fail(f"Unexpected arguments: {' '.join(positional)}")
    fmt = options.get("--format", [None])[-1]
    if fmt not in ("json", "csv"):
        fail("Usage: export --format json|csv")
    state = load()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        records = [
            {"id": t["id"], "title": t["title"], "done": bool(t.get("done")),
             "priority": task_priority(t), "tags": task_tags(t), "due": task_due(t)}
            for t in tasks
        ]
        print(json.dumps(records, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for t in tasks:
        row = [str(t["id"]), t["title"], "true" if t.get("done") else "false",
               task_priority(t), ";".join(task_tags(t)), task_due(t) or ""]
        print(",".join(row))


def cmd_stats(args):
    if args:
        fail("Usage: stats")
    state = load()
    tasks = state["tasks"]
    done = sum(1 for t in tasks if t.get("done"))
    total = len(tasks)
    print(f"open: {total - done}")
    print(f"done: {done}")
    print(f"total: {total}")


def cmd_undo(args):
    if args:
        fail("Usage: undo")
    state = load()
    history = state.get("history", [])
    if not history:
        fail("Nothing to undo")
    snap = history.pop()
    state["next_id"] = snap["next_id"]
    state["tasks"] = snap["tasks"]
    state["history"] = history
    save(state)
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


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        fail("Usage: tasks.py <command> [args]")
    COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
