#!/usr/bin/env python3
"""Command-line task manager. Stores data in tasks.json in the CWD."""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

DATA_FILE = "tasks.json"
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


class Fail(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Fail(message)

    def exit(self, status=0, message=None):
        if status:
            raise Fail(message or "error")
        raise SystemExit(0)


def empty_state():
    return {"next_id": 1, "tasks": [], "history": []}


def load():
    if not os.path.exists(DATA_FILE):
        return empty_state()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError) as e:
        raise Fail("Corrupt data file: %s" % e)
    if not isinstance(state, dict):
        raise Fail("Corrupt data file")
    state.setdefault("next_id", 1)
    state.setdefault("tasks", [])
    state.setdefault("history", [])
    return state


def save(state):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, DATA_FILE)


def snapshot(state):
    return {"next_id": state["next_id"], "tasks": json.loads(json.dumps(state["tasks"]))}


def mutate(state):
    """Record the current state in history before a mutating command."""
    state["history"].append(snapshot(state))


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        raise Fail("Invalid date: %s" % value)
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise Fail("Invalid date: %s" % value)
    return value


def valid_priority(value):
    if value not in PRIORITY_RANK:
        raise Fail("Invalid priority: %s" % value)
    return value


def find(state, tid):
    for t in state["tasks"]:
        if t["id"] == tid:
            return t
    raise Fail("No such task: %d" % tid)


def format_line(t):
    box = "[x]" if t["done"] else "[ ]"
    parts = ["%d %s %s" % (t["id"], box, t["title"])]
    if t.get("priority", "medium") != "medium":
        parts.append("(%s)" % t["priority"])
    if t.get("tags"):
        parts.append(" ".join("#" + tag for tag in t["tags"]))
    if t.get("due"):
        parts.append("due:" + t["due"])
    return " ".join(parts)


def cmd_add(state, args):
    priority = valid_priority(args.priority)
    due = valid_date(args.due) if args.due is not None else None
    title = " ".join(args.title)
    mutate(state)
    tid = state["next_id"]
    state["next_id"] = tid + 1
    state["tasks"].append({
        "id": tid, "title": title, "done": False,
        "priority": priority, "tags": list(args.tag or []), "due": due,
    })
    return "Added %d" % tid


def cmd_list(state, args):
    tasks = list(state["tasks"])
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]
    if args.overdue:
        today = args.today or datetime.date.today().isoformat()
        valid_date(today)
        tasks = [t for t in tasks
                 if not t["done"] and t.get("due") and t["due"] < today]
    if args.sort == "priority":
        tasks.sort(key=lambda t: (PRIORITY_RANK.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        return "No tasks"
    return "\n".join(format_line(t) for t in tasks)


def cmd_done(state, args):
    t = find(state, args.id)
    mutate(state)
    t["done"] = True
    return "Done %d" % args.id


def cmd_delete(state, args):
    find(state, args.id)
    mutate(state)
    state["tasks"] = [t for t in state["tasks"] if t["id"] != args.id]
    return "Deleted %d" % args.id


def cmd_edit(state, args):
    find(state, args.id)
    title = " ".join(args.title)
    mutate(state)
    find(state, args.id)["title"] = title
    return "Edited %d" % args.id


def cmd_search(state, args):
    needle = args.text.lower()
    matches = [t for t in state["tasks"] if needle in t["title"].lower()]
    if not matches:
        return "No matches"
    return "\n".join(format_line(t) for t in matches)


def cmd_export(state, args):
    if args.format == "json":
        out = [{
            "id": t["id"], "title": t["title"], "done": bool(t["done"]),
            "priority": t.get("priority", "medium"),
            "tags": list(t.get("tags", [])), "due": t.get("due"),
        } for t in state["tasks"]]
        return json.dumps(out, indent=2)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "title", "done", "priority", "tags", "due"])
    for t in state["tasks"]:
        w.writerow([
            t["id"], t["title"], "true" if t["done"] else "false",
            t.get("priority", "medium"), ";".join(t.get("tags", [])),
            t.get("due") or "",
        ])
    return buf.getvalue().rstrip("\n")


def cmd_stats(state, args):
    total = len(state["tasks"])
    done = sum(1 for t in state["tasks"] if t["done"])
    return "open: %d\ndone: %d\ntotal: %d" % (total - done, done, total)


def cmd_undo(state, args):
    if not state["history"]:
        raise Fail("Nothing to undo")
    snap = state["history"].pop()
    state["next_id"] = snap["next_id"]
    state["tasks"] = snap["tasks"]
    return "Undone"


def build_parser():
    p = Parser(prog="tasks.py")
    sub = p.add_subparsers(dest="command")
    sub.required = True

    a = sub.add_parser("add")
    a.add_argument("title", nargs="+")
    a.add_argument("--priority", default="medium")
    a.add_argument("--tag", action="append")
    a.add_argument("--due")

    l = sub.add_parser("list")
    l.add_argument("--sort", choices=["priority"])
    l.add_argument("--tag")
    l.add_argument("--overdue", action="store_true")
    l.add_argument("--today")

    for name in ("done", "delete"):
        s = sub.add_parser(name)
        s.add_argument("id", type=int)

    e = sub.add_parser("edit")
    e.add_argument("id", type=int)
    e.add_argument("--title", nargs="+", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")

    x = sub.add_parser("export")
    x.add_argument("--format", choices=["json", "csv"], required=True)

    sub.add_parser("stats")
    sub.add_parser("undo")
    return p


HANDLERS = {
    "add": cmd_add, "list": cmd_list, "done": cmd_done, "delete": cmd_delete,
    "edit": cmd_edit, "search": cmd_search, "export": cmd_export,
    "stats": cmd_stats, "undo": cmd_undo,
}
MUTATING = {"add", "done", "delete", "edit"}


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        state = load()
        out = HANDLERS[args.command](state, args)
        if args.command in MUTATING or args.command == "undo":
            save(state)
        if out:
            print(out)
        return 0
    except Fail as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
