#!/usr/bin/env python3
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

DATA_FILE = "tasks.json"


class Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(message + "\n")
        sys.exit(1)


def fail(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "history": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, DATA_FILE)


def snapshot(state):
    return {"next_id": state["next_id"], "tasks": json.loads(json.dumps(state["tasks"]))}


def record(state, snap):
    state["history"].append(snap)


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        fail("Invalid date: " + value)
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        fail("Invalid date: " + value)
    return value


def task_line(t):
    s = "%d [%s] %s" % (t["id"], "x" if t["done"] else " ", t["title"])
    if t["priority"] != "medium":
        s += " (%s)" % t["priority"]
    if t["tags"]:
        s += " " + " ".join("#" + g for g in t["tags"])
    if t.get("due"):
        s += " due:" + t["due"]
    return s


def find(state, tid):
    for t in state["tasks"]:
        if t["id"] == tid:
            return t
    fail("No such task: %d" % tid)


PRIO_RANK = {"high": 0, "medium": 1, "low": 2}


def cmd_add(args):
    state = load()
    if args.priority not in PRIO_RANK:
        fail("Invalid priority: " + args.priority)
    due = valid_date(args.due) if args.due is not None else None
    snap = snapshot(state)
    tid = state["next_id"]
    state["next_id"] = tid + 1
    state["tasks"].append({
        "id": tid,
        "title": " ".join(args.title),
        "done": False,
        "priority": args.priority,
        "tags": list(args.tag or []),
        "due": due,
    })
    record(state, snap)
    save(state)
    print("Added %d" % tid)


def cmd_list(args):
    state = load()
    tasks = list(state["tasks"])
    if args.tag:
        tasks = [t for t in tasks if args.tag in t["tags"]]
    if args.overdue:
        today = args.today or datetime.date.today().isoformat()
        valid_date(today)
        tasks = [t for t in tasks if not t["done"] and t["due"] and t["due"] < today]
    if args.sort == "priority":
        tasks.sort(key=lambda t: (PRIO_RANK[t["priority"]], t["id"]))
    else:
        tasks.sort(key=lambda t: t["id"])
    if not tasks:
        print("No tasks")
        return
    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    state = load()
    t = find(state, args.id)
    snap = snapshot(state)
    t["done"] = True
    record(state, snap)
    save(state)
    print("Done %d" % args.id)


def cmd_delete(args):
    state = load()
    find(state, args.id)
    snap = snapshot(state)
    state["tasks"] = [t for t in state["tasks"] if t["id"] != args.id]
    record(state, snap)
    save(state)
    print("Deleted %d" % args.id)


def cmd_edit(args):
    state = load()
    find(state, args.id)
    snap = snapshot(state)
    t = find(state, args.id)
    t["title"] = " ".join(args.title)
    record(state, snap)
    save(state)
    print("Edited %d" % args.id)


def cmd_search(args):
    state = load()
    needle = args.text.lower()
    tasks = sorted(
        (t for t in state["tasks"] if needle in t["title"].lower()),
        key=lambda t: t["id"],
    )
    if not tasks:
        print("No matches")
        return
    for t in tasks:
        print(task_line(t))


def cmd_export(args):
    state = load()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if args.format == "json":
        out = [
            {
                "id": t["id"],
                "title": t["title"],
                "done": bool(t["done"]),
                "priority": t["priority"],
                "tags": list(t["tags"]),
                "due": t["due"] if t.get("due") else None,
            }
            for t in tasks
        ]
        print(json.dumps(out, indent=2))
    else:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["id", "title", "done", "priority", "tags", "due"])
        for t in tasks:
            w.writerow([
                t["id"],
                t["title"],
                "true" if t["done"] else "false",
                t["priority"],
                ";".join(t["tags"]),
                t.get("due") or "",
            ])
        sys.stdout.write(buf.getvalue())


def cmd_stats(args):
    state = load()
    total = len(state["tasks"])
    done = sum(1 for t in state["tasks"] if t["done"])
    print("open: %d" % (total - done))
    print("done: %d" % done)
    print("total: %d" % total)


def cmd_undo(args):
    state = load()
    if not state["history"]:
        fail("Nothing to undo")
    snap = state["history"].pop()
    state["next_id"] = snap["next_id"]
    state["tasks"] = snap["tasks"]
    save(state)
    print("Undone")


def build_parser():
    p = Parser(prog="tasks.py")
    sub = p.add_subparsers(dest="command")
    sub.required = True

    a = sub.add_parser("add")
    a.add_argument("title", nargs="+")
    a.add_argument("--priority", default="medium")
    a.add_argument("--tag", action="append")
    a.add_argument("--due")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list")
    l.add_argument("--sort", choices=["priority", "id"], default="id")
    l.add_argument("--tag")
    l.add_argument("--overdue", action="store_true")
    l.add_argument("--today")
    l.set_defaults(func=cmd_list)

    d = sub.add_parser("done")
    d.add_argument("id", type=int)
    d.set_defaults(func=cmd_done)

    de = sub.add_parser("delete")
    de.add_argument("id", type=int)
    de.set_defaults(func=cmd_delete)

    e = sub.add_parser("edit")
    e.add_argument("id", type=int)
    e.add_argument("--title", nargs="+", required=True)
    e.set_defaults(func=cmd_edit)

    s = sub.add_parser("search")
    s.add_argument("text")
    s.set_defaults(func=cmd_search)

    ex = sub.add_parser("export")
    ex.add_argument("--format", choices=["json", "csv"], required=True)
    ex.set_defaults(func=cmd_export)

    st = sub.add_parser("stats")
    st.set_defaults(func=cmd_stats)

    u = sub.add_parser("undo")
    u.set_defaults(func=cmd_undo)
    return p


def main():
    p = build_parser()
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        fail("Error: %s" % exc)
