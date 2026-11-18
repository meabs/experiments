#!/usr/bin/env python3
"""Command-line task manager. Data stored in tasks.json in the cwd."""
import csv
import datetime
import io
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def parse_opts(args, valued):
    """Split args into positional words and --opt VALUE pairs.

    valued: names of options taking a value (repeatable ones collected in lists).
    Returns (positionals, opts) where opts maps name -> list of values.
    """
    pos, opts = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in valued:
            if i + 1 >= len(args):
                fail(f"Missing value for {a}")
            opts.setdefault(a[2:], []).append(args[i + 1])
            i += 2
        else:
            pos.append(a)
            i += 1
    return pos, opts


def validate_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        fail(f"Invalid date: {value}")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        fail(f"Invalid date: {value}")


def cmd_add(args):
    pos, opts = parse_opts(args, ("priority", "tag", "due"))
    if not pos:
        fail("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]")
    title = " ".join(pos)
    priority = opts.get("priority", ["medium"])[-1]
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = opts.get("tag", [])
    due = opts.get("due", [None])[-1]
    if due is not None:
        validate_date(due)
    data = load()
    task_id = data["next_id"]
    data["next_id"] = task_id + 1
    data["tasks"].append({"id": task_id, "title": title, "done": False,
                          "priority": priority, "tags": tags, "due": due})
    save(data)
    print(f"Added {task_id}")


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def parse_id(s):
    try:
        return int(s)
    except ValueError:
        fail(f"No such task: {s}")


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    task_id = parse_id(args[0])
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    t["done"] = True
    save(data)
    print(f"Done {task_id}")


def cmd_delete(args):
    if len(args) != 1:
        fail("Usage: delete ID")
    task_id = parse_id(args[0])
    data = load()
    if find_task(data, task_id) is None:
        fail(f"No such task: {task_id}")
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save(data)
    print(f"Deleted {task_id}")


def cmd_edit(args):
    if "--title" not in args:
        fail("Usage: edit ID --title NEW TITLE")
    i = args.index("--title")
    pos, title_words = args[:i], args[i + 1:]
    if len(pos) != 1 or not title_words:
        fail("Usage: edit ID --title NEW TITLE")
    task_id = parse_id(pos[0])
    data = load()
    t = find_task(data, task_id)
    if t is None:
        fail(f"No such task: {task_id}")
    t["title"] = " ".join(title_words)
    save(data)
    print(f"Edited {task_id}")


def cmd_search(args):
    if not args:
        fail("Usage: search TEXT")
    needle = " ".join(args).lower()
    data = load()
    matches = [t for t in sorted(data["tasks"], key=lambda t: t["id"])
               if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_line(t))


def cmd_export(args):
    _, opts = parse_opts(args, ("format",))
    fmt = opts.get("format", [None])[-1]
    if fmt not in ("json", "csv"):
        fail("Usage: export --format json|csv")
    data = load()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        out = [{"id": t["id"], "title": t["title"], "done": bool(t.get("done")),
                "priority": t.get("priority", "medium"), "tags": t.get("tags", []),
                "due": t.get("due")} for t in tasks]
        print(json.dumps(out, indent=2))
        return
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "title", "done", "priority", "tags", "due"])
    for t in tasks:
        w.writerow([t["id"], t["title"], "true" if t.get("done") else "false",
                    t.get("priority", "medium"), ";".join(t.get("tags", [])),
                    t.get("due") or ""])
    print(buf.getvalue(), end="")


def cmd_stats(args):
    data = load()
    tasks = data["tasks"]
    done = sum(1 for t in tasks if t.get("done"))
    print(f"open: {len(tasks) - done}")
    print(f"done: {done}")
    print(f"total: {len(tasks)}")


def format_line(t):
    mark = "x" if t.get("done") else " "
    line = f"{t['id']} [{mark}] {t['title']}"
    prio = t.get("priority", "medium")
    if prio != "medium":
        line += f" ({prio})"
    for tag in t.get("tags", []):
        line += f" #{tag}"
    if t.get("due"):
        line += f" due:{t['due']}"
    return line


def cmd_list(args):
    _, opts = parse_opts(args, ("sort", "tag", "today"))
    data = load()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if "--overdue" in args:
        today = opts.get("today", [None])[-1] or datetime.date.today().isoformat()
        validate_date(today)
        tasks = [t for t in tasks if not t.get("done") and t.get("due")
                 and t["due"] < today]
    if "tag" in opts:
        tasks = [t for t in tasks if all(g in t.get("tags", []) for g in opts["tag"])]
    if opts.get("sort", [None])[-1] == "priority":
        tasks.sort(key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 1))
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(format_line(t))


MUTATING = ("add", "done", "delete", "edit")


def cmd_undo(args):
    if args:
        fail("Usage: undo")
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
    "undo": cmd_undo,
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd, args = argv[0], argv[1:]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    before = None
    if cmd in MUTATING:
        d = load()
        before = {"next_id": d["next_id"], "tasks": d["tasks"]}
    COMMANDS[cmd](args)
    if before is not None:
        # Only reached when the command succeeded (failures call sys.exit first).
        d = load()
        d.setdefault("history", []).append(before)
        save(d)


if __name__ == "__main__":
    main(sys.argv[1:])
