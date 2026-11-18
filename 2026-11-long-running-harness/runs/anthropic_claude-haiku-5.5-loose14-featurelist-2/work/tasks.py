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


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        fail(f"Invalid date: {value}")
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        fail(f"Invalid date: {value}")
    return value


def parse_opts(args, flags):
    """Split args into positionals and a dict of option values.
    flags: set of option names (without --) that take one value; repeatable ones are lists."""
    positional, opts = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in flags:
            if i + 1 >= len(args):
                fail(f"Missing value for {a}")
            opts.setdefault(a[2:], []).append(args[i + 1])
            i += 2
        else:
            positional.append(a)
            i += 1
    return positional, opts


def cmd_add(args):
    positional, opts = parse_opts(args, {"priority", "tag", "due"})
    if not positional:
        fail("Usage: add TITLE")
    title = positional[0]
    priority = opts.get("priority", ["medium"])[-1]
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = list(opts.get("tag", []))
    due = parse_date(opts["due"][-1]) if "due" in opts else None
    data = load()
    task_id = data["next_id"]
    data["next_id"] = task_id + 1
    data["tasks"].append({"id": task_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due})
    save(data)
    print(f"Added {task_id}")


def format_task(t):
    mark = "x" if t["done"] else " "
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
    overdue = "--overdue" in args
    args = [a for a in args if a != "--overdue"]
    positional, opts = parse_opts(args, {"sort", "tag", "today"})
    data = load()
    if not data["tasks"]:
        print("No tasks")
        return
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    wanted = opts.get("tag", [])
    if wanted:
        tasks = [t for t in tasks if all(w in t.get("tags", []) for w in wanted)]
    if overdue:
        today = parse_date(opts["today"][-1]) if "today" in opts else datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today]
    sort = opts.get("sort", [None])[-1]
    if sort == "priority":
        tasks.sort(key=lambda t: PRIORITY_RANK.get(t.get("priority", "medium"), 1))
    elif sort is not None:
        fail(f"Invalid sort: {sort}")
    for t in tasks:
        print(format_task(t))


def cmd_search(args):
    if not args:
        fail("Usage: search TEXT")
    needle = " ".join(args).lower()
    data = load()
    matches = sorted((t for t in data["tasks"] if needle in t["title"].lower()), key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task(t))


def cmd_done(args):
    if not args:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    data = load()
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            save(data)
            print(f"Done {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_delete(args):
    if not args:
        fail("Usage: delete ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    data = load()
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            del data["tasks"][i]
            save(data)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_edit(args):
    if not args:
        fail("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    rest = args[1:]
    if "--title" not in rest or rest.index("--title") + 1 >= len(rest):
        fail("Usage: edit ID --title NEW TITLE")
    # --title consumes all following words (shell splits unquoted titles)
    new_title = " ".join(rest[rest.index("--title") + 1:])
    data = load()
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["title"] = new_title
            save(data)
            print(f"Edited {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_export(args):
    positional, opts = parse_opts(args, {"format"})
    fmt = opts.get("format", ["json"])[-1]
    if fmt not in ("json", "csv"):
        fail(f"Invalid format: {fmt}")
    data = load()
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    rows = [
        {
            "id": t["id"],
            "title": t["title"],
            "done": bool(t["done"]),
            "priority": t.get("priority", "medium"),
            "tags": list(t.get("tags", [])),
            "due": t.get("due") or None,
        }
        for t in tasks
    ]
    if fmt == "json":
        print(json.dumps(rows, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for r in rows:
        fields = [
            str(r["id"]),
            r["title"],
            "true" if r["done"] else "false",
            r["priority"],
            ";".join(r["tags"]),
            r["due"] or "",
        ]
        print(",".join(fields))


def cmd_stats(args):
    data = load()
    total = len(data["tasks"])
    done = sum(1 for t in data["tasks"] if t["done"])
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
}


def cmd_undo(args):
    data = load()
    history = data.get("history", [])
    if not history:
        fail("Nothing to undo")
    state = history.pop()
    data["next_id"] = state["next_id"]
    data["tasks"] = state["tasks"]
    data["history"] = history
    save(data)
    print("Undone")


COMMANDS["undo"] = cmd_undo
MUTATING = {"add", "done", "delete", "edit"}


def snapshot():
    data = load()
    return {"next_id": data["next_id"], "tasks": json.loads(json.dumps(data["tasks"]))}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd = argv[0]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    if cmd in MUTATING:
        before = snapshot()
        # Command calls fail() -> SystemExit on error, so failed commands are not recorded.
        COMMANDS[cmd](argv[1:])
        data = load()
        data.setdefault("history", []).append(before)
        save(data)
        return
    COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
