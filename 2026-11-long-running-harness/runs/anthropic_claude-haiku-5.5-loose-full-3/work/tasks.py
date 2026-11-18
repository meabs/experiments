#!/usr/bin/env python3
"""Command-line task manager. Data is stored in tasks.json in the cwd."""
import argparse
import copy
import csv
import datetime
import io
import json
import os
import sys

DATA_FILE = "tasks.json"
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class TaskError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise TaskError(message)


def load():
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "tasks": [], "undo": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("undo", [])
    return data


def save(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_FILE)


def validate_date(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise TaskError("Invalid date: %s" % value)
    return value


def format_line(t):
    parts = ["%d" % t["id"], "[x]" if t["done"] else "[ ]", t["title"]]
    line = " ".join(parts)
    if t.get("priority", "medium") != "medium":
        line += " (%s)" % t["priority"]
    if t.get("tags"):
        line += " " + " ".join("#" + tag for tag in t["tags"])
    if t.get("due"):
        line += " due:%s" % t["due"]
    return line


def find(data, tid):
    for t in data["tasks"]:
        if t["id"] == tid:
            return t
    raise TaskError("No such task: %s" % tid)


def snapshot(data):
    return {"next_id": data["next_id"], "tasks": copy.deepcopy(data["tasks"])}


def record(data, snap):
    data["undo"].append(snap)


def cmd_add(args, data, out):
    title = " ".join(args.title)
    if args.priority not in PRIORITY_ORDER:
        raise TaskError("Invalid priority: %s" % args.priority)
    dues = args.due or None
    if dues is not None:
        validate_date(dues)
    snap = snapshot(data)
    tid = data["next_id"]
    data["next_id"] = tid + 1
    data["tasks"].append({
        "id": tid,
        "title": title,
        "done": False,
        "priority": args.priority,
        "tags": list(args.tag or []),
        "due": dues,
    })
    record(data, snap)
    out.append("Added %d" % tid)


def cmd_list(args, data, out):
    tasks = list(data["tasks"])
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.get("tags", [])]
    if args.overdue:
        today = args.today or datetime.date.today().isoformat()
        validate_date(today)
        tasks = [t for t in tasks
                 if not t["done"] and t.get("due") and t["due"] < today]
    if args.sort == "priority":
        tasks.sort(key=lambda t: (PRIORITY_ORDER[t.get("priority", "medium")], t["id"]))
    if not tasks:
        out.append("No tasks")
        return
    for t in tasks:
        out.append(format_line(t))


def cmd_done(args, data, out):
    t = find(data, args.id)
    snap = snapshot(data)
    t["done"] = True
    record(data, snap)
    out.append("Done %d" % args.id)


def cmd_delete(args, data, out):
    find(data, args.id)
    snap = snapshot(data)
    data["tasks"] = [t for t in data["tasks"] if t["id"] != args.id]
    record(data, snap)
    out.append("Deleted %d" % args.id)


def cmd_edit(args, data, out):
    t = find(data, args.id)
    snap = snapshot(data)
    t["title"] = " ".join(args.title)
    record(data, snap)
    out.append("Edited %d" % args.id)


def cmd_search(args, data, out):
    needle = args.text.lower()
    matches = [t for t in data["tasks"] if needle in t["title"].lower()]
    if not matches:
        out.append("No matches")
        return
    for t in matches:
        out.append(format_line(t))


def export_records(data):
    recs = []
    for t in data["tasks"]:
        recs.append({
            "id": t["id"],
            "title": t["title"],
            "done": bool(t["done"]),
            "priority": t.get("priority", "medium"),
            "tags": list(t.get("tags", [])),
            "due": t.get("due") or None,
        })
    return recs


def cmd_export(args, data, out):
    recs = export_records(data)
    if args.format == "json":
        out.append(json.dumps(recs, indent=2))
    elif args.format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["id", "title", "done", "priority", "tags", "due"])
        for r in recs:
            w.writerow([
                r["id"], r["title"], "true" if r["done"] else "false",
                r["priority"], ";".join(r["tags"]), r["due"] or "",
            ])
        out.append(buf.getvalue().rstrip("\n"))
    else:
        raise TaskError("Invalid format: %s" % args.format)


def cmd_stats(args, data, out):
    total = len(data["tasks"])
    done = sum(1 for t in data["tasks"] if t["done"])
    out.append("open: %d" % (total - done))
    out.append("done: %d" % done)
    out.append("total: %d" % total)


def cmd_undo(args, data, out):
    if not data["undo"]:
        raise TaskError("Nothing to undo")
    snap = data["undo"].pop()
    data["next_id"] = snap["next_id"]
    data["tasks"] = snap["tasks"]
    out.append("Undone")


MUTATING = {"add", "done", "delete", "edit"}
HANDLERS = {
    "add": cmd_add, "list": cmd_list, "done": cmd_done,
    "delete": cmd_delete, "edit": cmd_edit, "search": cmd_search,
    "export": cmd_export, "stats": cmd_stats, "undo": cmd_undo,
}


def build_parser():
    p = _Parser(prog="tasks.py")
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

    d = sub.add_parser("done")
    d.add_argument("id", type=int)

    dl = sub.add_parser("delete")
    dl.add_argument("id", type=int)

    e = sub.add_parser("edit")
    e.add_argument("id", type=int)
    e.add_argument("--title", nargs="+", required=True)

    s = sub.add_parser("search")
    s.add_argument("text")

    x = sub.add_parser("export")
    x.add_argument("--format", default="json")

    sub.add_parser("stats")
    sub.add_parser("undo")
    return p


def run(argv):
    out = []
    try:
        args = build_parser().parse_args(argv)
        data = load()
        HANDLERS[args.command](args, data, out)
        if args.command in MUTATING or args.command == "undo":
            save(data)
    except TaskError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    for line in out:
        print(line)
    return 0


def main():
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
