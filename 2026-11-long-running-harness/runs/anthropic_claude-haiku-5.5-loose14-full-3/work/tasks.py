#!/usr/bin/env python3
"""tasks.py - a small command-line task manager (stdlib only)."""
import copy
import datetime
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


def load_store():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        store = json.load(f)
    store.setdefault("history", [])
    return store


def save_store(store):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def snapshot(store):
    """Pre-mutation state needed to undo a change."""
    return copy.deepcopy({"next_id": store["next_id"], "tasks": store["tasks"]})


def save_mutation(store, before):
    """Record the pre-mutation snapshot in history, then save."""
    store.setdefault("history", []).append(before)
    save_store(store)


def fail(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def cmd_add(args):
    title = None
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--due":
            if i + 1 >= len(args):
                fail("Usage: add TITLE [--due YYYY-MM-DD]")
            due = args[i + 1]
            if not valid_date(due):
                fail(f"Invalid date: {due}")
            i += 2
            continue
        if a == "--priority":
            if i + 1 >= len(args):
                fail("Usage: add TITLE [--priority high|medium|low]")
            priority = args[i + 1]
            if priority not in PRIORITIES:
                fail(f"Invalid priority: {priority}")
            i += 2
        elif a == "--tag":
            if i + 1 >= len(args):
                fail("Usage: add TITLE [--tag TAG]")
            tags.append(args[i + 1])
            i += 2
        elif a.startswith("--"):
            fail(f"Unknown option: {a}")
        else:
            if title is not None:
                fail("Usage: add TITLE [--priority high|medium|low]")
            title = a
            i += 1
    if title is None:
        fail("Usage: add TITLE [--priority high|medium|low]")
    store = load_store()
    before = snapshot(store)
    task_id = store["next_id"]
    store["next_id"] = task_id + 1
    store["tasks"].append({"id": task_id, "title": title, "done": False,
                           "priority": priority, "tags": tags, "due": due})
    save_mutation(store, before)
    print(f"Added {task_id}")


def format_task(t):
    mark = "x" if t["done"] else " "
    line = f"{t['id']} [{mark}] {t['title']}"
    pri = t.get("priority", "medium")
    if pri != "medium":
        line += f" ({pri})"
    for tag in t.get("tags", []):
        line += f" #{tag}"
    if t.get("due"):
        line += f" due:{t['due']}"
    return line


def cmd_list(args):
    sort = None
    tag = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args) and args[i + 1] == "priority":
            sort = "priority"
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today = args[i + 1]
            if not valid_date(today):
                fail(f"Invalid date: {today}")
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag = args[i + 1]
            i += 2
        else:
            fail(f"Unknown option: {args[i]}")
    tasks = load_store()["tasks"]
    if tag is not None:
        tasks = [t for t in tasks if tag in t.get("tags", [])]
    if overdue:
        if today is None:
            today = datetime.date.today().isoformat()
        tasks = [t for t in tasks if not t["done"] and t.get("due")
                 and t["due"] < today]
    if not tasks:
        print("No tasks")
        return
    if sort == "priority":
        key = lambda t: (PRIORITY_RANK.get(t.get("priority", "medium"), 1), t["id"])
    else:
        key = lambda t: t["id"]
    for t in sorted(tasks, key=key):
        print(format_task(t))


def cmd_search(args):
    if len(args) != 1:
        fail("Usage: search TEXT")
    needle = args[0].lower()
    tasks = [t for t in load_store()["tasks"] if needle in t["title"].lower()]
    if not tasks:
        print("No matches")
        return
    for t in sorted(tasks, key=lambda t: t["id"]):
        print(format_task(t))


def cmd_done(args):
    if len(args) != 1:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    store = load_store()
    before = snapshot(store)
    for t in store["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            save_mutation(store, before)
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
    store = load_store()
    before = snapshot(store)
    for i, t in enumerate(store["tasks"]):
        if t["id"] == task_id:
            del store["tasks"][i]
            save_mutation(store, before)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_edit(args):
    usage = "Usage: edit ID --title NEW TITLE"
    if len(args) < 3 or args[1] != "--title":
        fail(usage)
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    title = " ".join(args[2:])
    store = load_store()
    before = snapshot(store)
    for t in store["tasks"]:
        if t["id"] == task_id:
            t["title"] = title
            save_mutation(store, before)
            print(f"Edited {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_export(args):
    fmt = None
    if len(args) == 2 and args[0] == "--format":
        fmt = args[1]
    if fmt not in ("json", "csv"):
        fail("Usage: export --format json|csv")
    tasks = sorted(load_store()["tasks"], key=lambda t: t["id"])
    if fmt == "json":
        out = [{"id": t["id"], "title": t["title"], "done": bool(t["done"]),
                "priority": t.get("priority", "medium"), "tags": list(t.get("tags", [])),
                "due": t.get("due") or None} for t in tasks]
        print(json.dumps(out, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for t in tasks:
        row = [str(t["id"]), t["title"], "true" if t["done"] else "false",
               t.get("priority", "medium"), ";".join(t.get("tags", [])), t.get("due") or ""]
        print(",".join(row))


def cmd_stats(args):
    if args:
        fail("Usage: stats")
    tasks = load_store()["tasks"]
    done = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    print(f"open: {total - done}")
    print(f"done: {done}")
    print(f"total: {total}")


def cmd_undo(args):
    if args:
        fail("Usage: undo")
    store = load_store()
    history = store.get("history", [])
    if not history:
        fail("Nothing to undo")
    prev = history.pop()
    store["next_id"] = prev["next_id"]
    store["tasks"] = prev["tasks"]
    save_store(store)
    print("Undone")


COMMANDS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete, "edit": cmd_edit, "search": cmd_search, "export": cmd_export, "stats": cmd_stats, "undo": cmd_undo}


def main(argv):
    if not argv:
        fail("Usage: tasks.py <command> [args]")
    cmd = argv[0]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd}")
    COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
