#!/usr/bin/env python3
"""Command-line task manager. Data is stored in tasks.json in the cwd."""
import copy
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


def snapshot(state):
    return {"next_id": state["next_id"], "tasks": copy.deepcopy(state["tasks"])}


def record(state, snap):
    state.setdefault("history", []).append(snap)


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


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_opts(args, options):
    """Split args into positional words and --option VALUE pairs.

    `options` is the set of accepted option names (without dashes).
    Returns (positionals, {name: [values]}).
    """
    positional = []
    opts = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--") and arg[2:] in options:
            if i + 1 >= len(args):
                fail(f"Missing value for {arg}")
            opts.setdefault(arg[2:], []).append(args[i + 1])
            i += 2
        elif arg.startswith("--"):
            fail(f"Unknown option: {arg}")
        else:
            positional.append(arg)
            i += 1
    return positional, opts


def validate_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        fail(f"Invalid date: {value}")
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        fail(f"Invalid date: {value}")
    return value


def format_task(task):
    mark = "x" if task.get("done") else " "
    line = f"{task['id']} [{mark}] {task['title']}"
    priority = task.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    for tag in task.get("tags", []):
        line += f" #{tag}"
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def cmd_add(args):
    positional, opts = parse_opts(args, {"priority", "tag", "due"})
    if not positional:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]...")
    priority = opts.get("priority", ["medium"])[-1]
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = opts.get("tag", [])
    due = None
    if "due" in opts:
        due = validate_date(opts["due"][-1])
    title = " ".join(positional)
    state = load()
    record(state, snapshot(state))
    task_id = state["next_id"]
    state["next_id"] = task_id + 1
    state["tasks"].append(
        {"id": task_id, "title": title, "done": False, "priority": priority,
         "tags": tags, "due": due}
    )
    save(state)
    print(f"Added {task_id}")


def cmd_list(args):
    overdue = "--overdue" in args
    args = [a for a in args if a != "--overdue"]
    positional, opts = parse_opts(args, {"sort", "tag", "today"})
    if positional:
        fail(f"Unknown option: {positional[0]}")
    sort = opts.get("sort", [None])[-1]
    if sort not in (None, "priority", "id"):
        fail(f"Invalid sort: {sort}")
    if "today" in opts:
        today = validate_date(opts["today"][-1])
    else:
        today = datetime.date.today().isoformat()
    tasks = load()["tasks"]
    if not tasks:
        print("No tasks")
        return
    tasks = sorted(tasks, key=lambda t: t["id"])
    for tag in opts.get("tag", []):
        tasks = [t for t in tasks if tag in t.get("tags", [])]
    if overdue:
        tasks = [t for t in tasks if not t.get("done") and t.get("due")
                 and t["due"] < today]
    if not tasks:
        print("No tasks")
        return
    if sort == "priority":
        tasks.sort(
            key=lambda t: PRIORITY_RANK.get(t.get("priority", "medium"), 1)
        )
    for task in tasks:
        print(format_task(task))


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
            snap = snapshot(state)
            task["done"] = True
            record(state, snap)
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
            snap = snapshot(state)
            del state["tasks"][i]
            record(state, snap)
            save(state)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_edit(args):
    if "--title" not in args:
        fail("Usage: edit ID --title NEW TITLE")
    idx = args.index("--title")
    before, after = args[:idx], args[idx + 1:]
    if len(before) != 1:
        fail("Usage: edit ID --title NEW TITLE")
    if not after:
        fail("Missing value for --title")
    try:
        task_id = int(before[0])
    except ValueError:
        fail(f"No such task: {before[0]}")
    title = " ".join(after)
    state = load()
    for task in state["tasks"]:
        if task["id"] == task_id:
            snap = snapshot(state)
            task["title"] = title
            record(state, snap)
            save(state)
            print(f"Edited {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_search(args):
    if not args:
        fail("Usage: search TEXT")
    needle = " ".join(args).lower()
    tasks = sorted(load()["tasks"], key=lambda t: t["id"])
    matches = [t for t in tasks if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in matches:
        print(format_task(task))


def cmd_export(args):
    positional, opts = parse_opts(args, {"format"})
    if positional:
        fail(f"Unknown option: {positional[0]}")
    fmt = opts.get("format", [None])[-1]
    if fmt not in ("json", "csv"):
        fail(f"Invalid format: {fmt}")
    tasks = sorted(load()["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        out = [
            {"id": t["id"], "title": t["title"], "done": bool(t.get("done")),
             "priority": t.get("priority", "medium"),
             "tags": list(t.get("tags", [])), "due": t.get("due") or None}
            for t in tasks
        ]
        print(json.dumps(out, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for t in tasks:
        row = [
            str(t["id"]), t["title"], "true" if t.get("done") else "false",
            t.get("priority", "medium"), ";".join(t.get("tags", [])),
            t.get("due") or "",
        ]
        print(",".join(row))


def cmd_stats(args):
    if args:
        fail("Usage: stats")
    tasks = load()["tasks"]
    done = sum(1 for t in tasks if t.get("done"))
    total = len(tasks)
    print(f"open: {total - done}")
    print(f"done: {done}")
    print(f"total: {total}")


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
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd = argv[0]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
