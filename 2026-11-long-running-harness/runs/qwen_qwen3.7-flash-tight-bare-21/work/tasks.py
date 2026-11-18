#!/usr/bin/env python3
import sys
import json
import os
import copy
from datetime import date, datetime

DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    with open(DATA_FILE) as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_state(tasks, next_id):
    h = load_history()
    h.append({"tasks": copy.deepcopy(tasks), "next_id": next_id})
    if len(h) > 100:
        h = h[-100:]
    save_history(h)


def cmd_undo():
    h = load_history()
    if not h:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    s = h.pop()
    save_history(h)
    save_tasks(s["tasks"], s["next_id"])
    print("Undone")


def parse_args(args):
    cmd = args[0]
    rem = args[1:]
    opt = {
        "priority": None,
        "tags": [],
        "due": None,
        "sort": None,
        "tag_filter": None,
        "overdue": False,
        "today": None,
        "format": None,
        "new_title": None,
    }
    i = 0
    pos = []
    while i < len(rem):
        a = rem[i]
        if a == "--priority" and i + 1 < len(rem):
            opt["priority"] = rem[i + 1]
            i += 2
        elif a == "--tag" and i + 1 < len(rem):
            opt["tags"].append(rem[i + 1])
            i += 2
        elif a == "--due" and i + 1 < len(rem):
            opt["due"] = rem[i + 1]
            i += 2
        elif a == "--title" and i + 1 < len(rem):
            opt["new_title"] = " ".join(rem[i + 1:])
            break
        elif a == "--sort" and i + 1 < len(rem):
            opt["sort"] = rem[i + 1]
            i += 2
        elif a == "--overdue":
            opt["overdue"] = True
            i += 1
        elif a == "--today" and i + 1 < len(rem):
            opt["today"] = rem[i + 1]
            i += 2
        elif a == "--format" and i + 1 < len(rem):
            opt["format"] = rem[i + 1]
            i += 2
        else:
            pos.append(a)
            i += 1
    return cmd, opt, pos


def validate_date(ds):
    try:
        datetime.strptime(ds, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def fmt(task):
    parts = [f"{task['id']} [{'x' if task['done'] else ' '}] {task['title']}"]
    p = task.get("priority", "medium")
    if p == "high":
        parts.append("(high)")
    elif p == "low":
        parts.append("(low)")
    for t in task.get("tags", []):
        parts.append(f"#{t}")
    d = task.get("due")
    if d:
        parts.append(f"due:{d}")
    return " ".join(parts)


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)

    cmd, opt, pos = parse_args(args)

    if cmd == "undo":
        cmd_undo()
        return

    tasks, next_id = load_tasks()

    if cmd == "add":
        if not pos:
            print("Usage: tasks.py add TITLE", file=sys.stderr)
            sys.exit(1)
        title = " ".join(pos)
        pri = opt["priority"] if opt["priority"] else "medium"
        if pri not in ("high", "medium", "low"):
            print(f"Invalid priority: {pri}", file=sys.stderr)
            sys.exit(1)
        due = opt["due"]
        if due is not None and not validate_date(due):
            print(f"Invalid date: {due}", file=sys.stderr)
            sys.exit(1)
        task = {
            "id": next_id,
            "title": title,
            "done": False,
            "priority": pri,
            "tags": list(opt["tags"]),
            "due": due,
        }
        push_state(tasks, next_id)
        tasks.append(task)
        next_id += 1
        save_tasks(tasks, next_id)
        print(f"Added {task['id']}")

    elif cmd == "list":
        tf = opt.get("tag_filter")
        filtered = list(tasks)
        if tf:
            filtered = [t for t in filtered if tf in t.get("tags", [])]
        if opt.get("overdue"):
            ts = opt.get("today") or date.today().isoformat()
            if not validate_date(ts):
                print(f"Invalid date: {ts}", file=sys.stderr)
                sys.exit(1)
            today = datetime.strptime(ts, "%Y-%m-%d").date()
            filtered = [
                t for t in filtered
                if not t["done"]
                and t.get("due")
                and datetime.strptime(t["due"], "%Y-%m-%d").date() < today
            ]
        if not filtered:
            print("No tasks")
            return
        if opt.get("sort") == "priority":
            po = {"high": 0, "medium": 1, "low": 2}
            filtered = sorted(
                filtered, key=lambda t: (po.get(t.get("priority", "medium"), 1), t["id"])
            )
        for t in filtered:
            print(fmt(t))

    elif cmd == "done":
        if not pos:
            print("Usage: tasks.py done ID", file=sys.stderr)
            sys.exit(1)
        try:
            tid = int(pos[0])
        except ValueError:
            print(f"Invalid task id: {pos[0]}", file=sys.stderr)
            sys.exit(1)
        found = None
        for t in tasks:
            if t["id"] == tid:
                found = t
                break
        if found is None:
            print(f"No such task: {tid}", file=sys.stderr)
            sys.exit(1)
        push_state(tasks, next_id)
        found["done"] = True
        save_tasks(tasks, next_id)
        print(f"Done {tid}")

    elif cmd == "delete":
        if not pos:
            print("Usage: tasks.py delete ID", file=sys.stderr)
            sys.exit(1)
        try:
            tid = int(pos[0])
        except ValueError:
            print(f"Invalid task id: {pos[0]}", file=sys.stderr)
            sys.exit(1)
        found = None
        for t in tasks:
            if t["id"] == tid:
                found = t
                break
        if found is None:
            print(f"No such task: {tid}", file=sys.stderr)
            sys.exit(1)
        push_state(tasks, next_id)
        tasks = [t for t in tasks if t["id"] != tid]
        save_tasks(tasks, next_id)
        print(f"Deleted {tid}")

    elif cmd == "edit":
        if not pos:
            print("Usage: tasks.py edit ID --title NEW TITLE", file=sys.stderr)
            sys.exit(1)
        try:
            tid = int(pos[0])
        except ValueError:
            print(f"Invalid task id: {pos[0]}", file=sys.stderr)
            sys.exit(1)
        if opt["new_title"] is None:
            print("Usage: tasks.py edit ID --title NEW TITLE", file=sys.stderr)
            sys.exit(1)
        found = None
        for t in tasks:
            if t["id"] == tid:
                found = t
                break
        if found is None:
            print(f"No such task: {tid}", file=sys.stderr)
            sys.exit(1)
        push_state(tasks, next_id)
        found["title"] = opt["new_title"]
        save_tasks(tasks, next_id)
        print(f"Edited {tid}")

    elif cmd == "search":
        if not pos:
            print("Usage: tasks.py search TEXT", file=sys.stderr)
            sys.exit(1)
        query = " ".join(pos).lower()
        matches = [t for t in tasks if query in t["title"].lower()]
        if not matches:
            print("No matches")
            return
        for t in matches:
            print(fmt(t))

    elif cmd == "export":
        fmt_type = opt.get("format")
        if fmt_type is None:
            print("Usage: tasks.py export --format json|csv", file=sys.stderr)
            sys.exit(1)
        if fmt_type == "json":
            export_data = []
            for t in sorted(tasks, key=lambda x: x["id"]):
                export_data.append({
                    "id": t["id"],
                    "title": t["title"],
                    "done": t["done"],
                    "priority": t.get("priority", "medium"),
                    "tags": t.get("tags", []),
                    "due": t.get("due"),
                })
            print(json.dumps(export_data))
        elif fmt_type == "csv":
            print("id,title,done,priority,tags,due")
            for t in sorted(tasks, key=lambda x: x["id"]):
                tags_str = ";".join(t.get("tags", []))
                due_str = t.get("due") or ""
                done_str = "true" if t["done"] else "false"
                print(f"{t['id']},{t['title']},{done_str},{t.get('priority', 'medium')},{tags_str},{due_str}")
        else:
            print(f"Invalid format: {fmt_type}", file=sys.stderr)
            sys.exit(1)

    elif cmd == "stats":
        open_count = sum(1 for t in tasks if not t["done"])
        done_count = sum(1 for t in tasks if t["done"])
        total_count = len(tasks)
        print(f"open: {open_count}")
        print(f"done: {done_count}")
        print(f"total: {total_count}")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
