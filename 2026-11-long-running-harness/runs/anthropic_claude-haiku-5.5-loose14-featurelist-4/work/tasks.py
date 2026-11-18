#!/usr/bin/env python3
"""Command-line task manager. Data is stored in ./tasks.json."""
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


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record(data):
    """Snapshot the current state into the undo history (call before mutating)."""
    data.setdefault("history", []).append({
        "next_id": data["next_id"],
        "tasks": json.loads(json.dumps(data["tasks"])),
    })


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_opts(args, valued, repeatable=(), flags=()):
    """Split args into positionals and a dict of --option values (last one wins).
    Options named in `repeatable` collect all values into a list.
    Options named in `flags` are boolean and stored as True."""
    positional = []
    opts = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in flags:
            opts[a[2:]] = True
            i += 1
        elif a.startswith("--") and a[2:] in valued:
            if i + 1 >= len(args):
                fail(f"Missing value for {a}")
            if a[2:] in repeatable:
                opts.setdefault(a[2:], []).append(args[i + 1])
            else:
                opts[a[2:]] = args[i + 1]
            i += 2
        elif a.startswith("--"):
            fail(f"Unknown option: {a}")
        else:
            positional.append(a)
            i += 1
    return positional, opts


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(value):
    """Return the validated YYYY-MM-DD string, or fail with 'Invalid date'."""
    if not DATE_RE.match(value):
        fail(f"Invalid date: {value}")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        fail(f"Invalid date: {value}")
    return value


def cmd_add(args):
    pos, opts = parse_opts(args, ("priority", "tag", "due"), repeatable=("tag",))
    if not pos:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = pos[0]
    priority = opts.get("priority", "medium")
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = opts.get("tag", [])
    due = parse_date(opts["due"]) if "due" in opts else None
    data = load()
    record(data)
    task_id = data["next_id"]
    data["next_id"] = task_id + 1
    data["tasks"].append({"id": task_id, "title": title, "done": False,
                          "priority": priority, "tags": tags, "due": due})
    save(data)
    print(f"Added {task_id}")


def task_line(t):
    mark = "x" if t["done"] else " "
    line = f"{t['id']} [{mark}] {t['title']}"
    priority = t.get("priority", "medium")
    if priority != "medium":
        line += f" ({priority})"
    for tag in t.get("tags", []):
        line += f" #{tag}"
    if t.get("due"):
        line += f" due:{t['due']}"
    return line


def cmd_list(args):
    pos, opts = parse_opts(args, ("sort", "tag", "today"), flags=("overdue",))
    if pos:
        fail(f"Unexpected argument: {pos[0]}")
    sort = opts.get("sort")
    if sort not in (None, "priority", "id"):
        fail(f"Invalid sort: {sort}")
    today = parse_date(opts["today"]) if "today" in opts else datetime.date.today().isoformat()
    data = load()
    if not data["tasks"]:
        print("No tasks")
        return
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if "tag" in opts:
        tasks = [t for t in tasks if opts["tag"] in t.get("tags", [])]
    if opts.get("overdue"):
        tasks = [t for t in tasks if not t["done"] and t.get("due")
                 and t["due"] < today]
    if not tasks:
        print("No tasks")
        return
    if sort == "priority":
        tasks = sorted(tasks, key=lambda t: PRIORITY_RANK.get(
            t.get("priority", "medium"), 1))
    for t in tasks:
        print(task_line(t))


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def parse_id(args, usage="Usage: done ID"):
    if not args:
        fail(usage)
    try:
        return int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")


def cmd_done(args):
    task_id = parse_id(args)
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    record(data)
    t["done"] = True
    save(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    task_id = parse_id(args, "Usage: delete ID")
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    record(data)
    data["tasks"].remove(t)
    save(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    usage = "Usage: edit ID --title NEW TITLE"
    if len(args) < 3 or args[1] != "--title":
        fail(usage)
    task_id = parse_id(args[:1], usage)
    title = " ".join(args[2:])
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    record(data)
    t["title"] = title
    save(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        fail("Usage: search TEXT")
    needle = args[0].lower()
    data = load()
    matches = [t for t in sorted(data["tasks"], key=lambda t: t["id"])
               if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(task_line(t))


def cmd_export(args):
    pos, opts = parse_opts(args, ("format",))
    if pos:
        fail(f"Unexpected argument: {pos[0]}")
    fmt = opts.get("format")
    if fmt not in ("json", "csv"):
        fail("Usage: export --format json|csv")
    data = load()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    rows = [{
        "id": t["id"],
        "title": t["title"],
        "done": bool(t["done"]),
        "priority": t.get("priority", "medium"),
        "tags": list(t.get("tags", [])),
        "due": t.get("due") or None,
    } for t in tasks]
    if fmt == "json":
        print(json.dumps(rows, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for r in rows:
        print(",".join([
            str(r["id"]), r["title"], "true" if r["done"] else "false",
            r["priority"], ";".join(r["tags"]), r["due"] or "",
        ]))


def cmd_stats(args):
    if args:
        fail(f"Unexpected argument: {args[0]}")
    data = load()
    total = len(data["tasks"])
    done = sum(1 for t in data["tasks"] if t["done"])
    print(f"open: {total - done}")
    print(f"done: {done}")
    print(f"total: {total}")


def cmd_undo(args):
    if args:
        fail(f"Unexpected argument: {args[0]}")
    data = load()
    history = data.get("history", [])
    if not history:
        fail("Nothing to undo")
    snap = history.pop()
    data["next_id"] = snap["next_id"]
    data["tasks"] = snap["tasks"]
    data["history"] = history
    save(data)
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
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd = argv[0]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
