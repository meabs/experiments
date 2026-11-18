#!/usr/bin/env python3
"""Command-line task manager. Data is stored in tasks.json in the cwd."""
import datetime
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


def load_state():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("history", [])
    return state


def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


REPEATABLE = ("--tag",)


def parse_options(args, valid):
    """Split args into positionals and options. valid maps --name -> takes_value.
    Repeatable options (REPEATABLE) collect their values into a list."""
    positional, opts = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a in valid:
            if valid[a]:
                if i + 1 >= len(args):
                    fail(f"Missing value for {a}")
                if a in REPEATABLE:
                    opts.setdefault(a, []).append(args[i + 1])
                else:
                    opts[a] = args[i + 1]
                i += 2
            else:
                opts[a] = True
                i += 1
        elif a.startswith("--"):
            fail(f"Unknown option: {a}")
        else:
            positional.append(a)
            i += 1
    return positional, opts


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(value):
    """Return value if it is a valid YYYY-MM-DD date, else fail."""
    if not DATE_RE.match(value):
        fail(f"Invalid date: {value}")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        fail(f"Invalid date: {value}")
    return value


def cmd_add(args):
    pos, opts = parse_options(args, {"--priority": True, "--tag": True, "--due": True})
    if not pos:
        fail("Usage: add TITLE")
    title = pos[0]
    priority = opts.get("--priority", "medium")
    if priority not in PRIORITIES:
        fail(f"Invalid priority: {priority}")
    tags = opts.get("--tag", [])
    due = parse_date(opts["--due"]) if "--due" in opts else None
    state = load_state()
    task_id = state["next_id"]
    state["tasks"].append({"id": task_id, "title": title, "done": False,
                           "priority": priority, "tags": tags, "due": due})
    state["next_id"] = task_id + 1
    save_state(state)
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
    pos, opts = parse_options(args, {"--sort": True, "--tag": True,
                                     "--overdue": False, "--today": True})
    if pos:
        fail(f"Unknown option: {pos[0]}")
    sort = opts.get("--sort")
    if sort is not None and sort != "priority":
        fail(f"Invalid sort: {sort}")
    today = None
    if "--today" in opts:
        today = parse_date(opts["--today"])
    elif "--overdue" in opts:
        today = datetime.date.today().isoformat()
    state = load_state()
    if not state["tasks"]:
        print("No tasks")
        return
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if "--tag" in opts:
        wanted = opts["--tag"]
        tasks = [t for t in tasks if all(w in t.get("tags", []) for w in wanted)]
    if "--overdue" in opts:
        tasks = [t for t in tasks
                 if not t["done"] and t.get("due") and t["due"] < today]
    if sort == "priority":
        tasks.sort(key=lambda t: PRIORITY_RANK[t.get("priority", "medium")])
    for t in tasks:
        print(format_task(t))


def cmd_done(args):
    if not args:
        fail("Usage: done ID")
    try:
        task_id = int(args[0])
    except ValueError:
        fail(f"No such task: {args[0]}")
    state = load_state()
    for t in state["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            save_state(state)
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
    state = load_state()
    for i, t in enumerate(state["tasks"]):
        if t["id"] == task_id:
            del state["tasks"][i]
            save_state(state)
            print(f"Deleted {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_edit(args):
    if not args or "--title" not in args:
        fail("Usage: edit ID --title NEW TITLE")
    idx = args.index("--title")
    before = [a for a in args[:idx] if a]
    title_words = args[idx + 1:]
    if not before:
        fail("Usage: edit ID --title NEW TITLE")
    try:
        task_id = int(before[0])
    except ValueError:
        fail(f"No such task: {before[0]}")
    if not title_words:
        fail("Usage: edit ID --title NEW TITLE")
    title = " ".join(title_words)
    state = load_state()
    for t in state["tasks"]:
        if t["id"] == task_id:
            t["title"] = title
            save_state(state)
            print(f"Edited {task_id}")
            return
    fail(f"No such task: {task_id}")


def cmd_search(args):
    if not args:
        fail("Usage: search TEXT")
    needle = args[0].lower()
    state = load_state()
    matches = [t for t in sorted(state["tasks"], key=lambda t: t["id"])
               if needle in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task(t))


def cmd_export(args):
    pos, opts = parse_options(args, {"--format": True})
    if pos:
        fail(f"Unknown option: {pos[0]}")
    fmt = opts.get("--format")
    if fmt not in ("json", "csv"):
        fail("Usage: export --format json|csv")
    state = load_state()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    rows = [{"id": t["id"], "title": t["title"], "done": bool(t["done"]),
             "priority": t.get("priority", "medium"), "tags": list(t.get("tags", [])),
             "due": t.get("due") or None} for t in tasks]
    if fmt == "json":
        print(json.dumps(rows, indent=2))
        return
    print("id,title,done,priority,tags,due")
    for r in rows:
        fields = [str(r["id"]), r["title"], "true" if r["done"] else "false",
                  r["priority"], ";".join(r["tags"]), r["due"] or ""]
        print(",".join(fields))


def cmd_stats(args):
    if args:
        fail(f"Unknown option: {args[0]}")
    state = load_state()
    total = len(state["tasks"])
    done = sum(1 for t in state["tasks"] if t["done"])
    print(f"open: {total - done}")
    print(f"done: {done}")
    print(f"total: {total}")




MUTATING = ("add", "done", "delete", "edit")


def cmd_undo(args):
    if args:
        fail("Usage: undo")
    state = load_state()
    history = state.get("history", [])
    if not history:
        fail("Nothing to undo")
    snap = history.pop()
    state["tasks"] = snap["tasks"]
    state["next_id"] = snap["next_id"]
    state["history"] = history
    save_state(state)
    print("Undone")


COMMANDS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete,
            "edit": cmd_edit, "search": cmd_search, "export": cmd_export,
            "stats": cmd_stats, "undo": cmd_undo}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        fail("Usage: tasks.py <add|...> [args]")
    name = argv[0]
    if name not in MUTATING:
        COMMANDS[name](argv[1:])
        return
    # Snapshot the state before a mutation; recorded only if the command succeeds
    # (failures call sys.exit before returning here).
    before = load_state()
    snap = {"next_id": before["next_id"], "tasks": json.loads(json.dumps(before["tasks"]))}
    COMMANDS[name](argv[1:])
    state = load_state()
    state.setdefault("history", []).append(snap)
    save_state(state)


if __name__ == "__main__":
    main(sys.argv[1:])
