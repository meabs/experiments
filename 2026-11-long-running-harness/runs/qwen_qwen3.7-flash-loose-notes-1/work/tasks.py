#!/usr/bin/env python3
"""Command-line task manager."""
import json
import os
import sys
from datetime import date

DATA_FILE = "tasks.json"
UNDO_FILE = "undo_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return data["tasks"], data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return {}, 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_undo_history():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, TypeError):
        return []


def save_undo_history(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def record_undo(tasks, next_id):
    history = load_undo_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_undo_history(history)


def undo_last():
    history = load_undo_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = history.pop()
    save_tasks(state["tasks"], state["next_id"])
    save_undo_history(history)
    print("Undone")


def format_task(task):
    check = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], check, task["title"])
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        line += " " + " ".join("#{}".format(t) for t in tags)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line

def parse_add_args(args):
    title_parts = []
    priority = "medium"
    tags = []
    due = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--priority":
            if i + 1 >= len(args):
                print("Missing value for --priority", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print("Invalid priority: {}".format(priority), file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif arg == "--due":
            if i + 1 >= len(args):
                print("Missing value for --due", file=sys.stderr)
                sys.exit(1)
            due_str = args[i + 1]
            try:
                parts = due_str.split("-")
                if len(parts) != 3:
                    raise ValueError
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
                due = due_str
            except (ValueError, OverflowError):
                print("Invalid date: {}".format(due_str), file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(arg)
            i += 1
    return title_parts, priority, tags, due


def cmd_add(args):
    if not args:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title_parts, priority, tags, due = parse_add_args(args)
    if not title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    record_undo(tasks, next_id)
    task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    tasks[next_id] = task
    next_id += 1
    save_tasks(tasks, next_id)
    print("Added {}".format(task["id"]))


def _get_task_key(tasks, task_id):
    """Get string key for task lookup."""
    sk = str(task_id)
    if sk not in tasks:
        # Try to find by matching id value
        for k, v in tasks.items():
            if v.get("id") == task_id:
                return k
    return sk


def cmd_list(args):
    tasks, _ = load_tasks()
    sort_mode = None
    tag_filter = None
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--sort":
            if i + 1 >= len(args):
                print("Missing value for --sort", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif arg == "--tag":
            if i + 1 >= len(args):
                print("Missing value for --tag", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif arg == "--overdue":
            overdue = True
            i += 1
        elif arg == "--today":
            if i + 1 >= len(args):
                print("Missing value for --today", file=sys.stderr)
                sys.exit(1)
            today_str = args[i + 1]
            i += 2
        else:
            print("Unknown option: {}".format(arg), file=sys.stderr)
            sys.exit(1)

    task_list = list(tasks.values())

    if tag_filter:
        task_list = [t for t in task_list if tag_filter in t.get("tags", [])]

    if overdue:
        if today_str:
            try:
                tp = today_str.split("-")
                today_date = date(int(tp[0]), int(tp[1]), int(tp[2]))
            except (ValueError, IndexError):
                print("Invalid date: {}".format(today_str), file=sys.stderr)
                sys.exit(1)
        else:
            today_date = date.today()
        filtered = []
        for t in task_list:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    dp = t["due"].split("-")
                    due_d = date(int(dp[0]), int(dp[1]), int(dp[2]))
                    if due_d < today_date:
                        filtered.append(t)
                except (ValueError, IndexError):
                    pass
        task_list = filtered

    if sort_mode == "priority":
        porder = {"high": 0, "medium": 1, "low": 2}
        task_list.sort(key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        task_list.sort(key=lambda t: t["id"])

    if not task_list:
        print("No tasks")
        return

    for t in task_list:
        print(format_task(t))


def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    key = _get_task_key(tasks, task_id)
    if key is None or key not in tasks:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    record_undo(tasks, next_id)
    tasks[key]["done"] = True
    save_tasks(tasks, next_id)
    print("Done {}".format(task_id))


def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    key = _get_task_key(tasks, task_id)
    if key is None or key not in tasks:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    record_undo(tasks, next_id)
    del tasks[key]
    save_tasks(tasks, next_id)
    print("Deleted {}".format(task_id))


def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("Invalid id: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)

    tasks, next_id = load_tasks()
    key = _get_task_key(tasks, task_id)
    if key is None or key not in tasks:
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)

    new_title_parts = []
    i = 1
    found_title = False
    while i < len(args):
        if args[i] == "--title":
            found_title = True
            i += 1
            break
        else:
            print("Unknown option: {}".format(args[i]), file=sys.stderr)
            sys.exit(1)

    if not found_title or i >= len(args):
        print("Missing title after --title", file=sys.stderr)
        sys.exit(1)

    while i < len(args):
        if args[i].startswith("--"):
            print("Unknown option: {}".format(args[i]), file=sys.stderr)
            sys.exit(1)
        new_title_parts.append(args[i])
        i += 1

    if not new_title_parts:
        print("Missing title", file=sys.stderr)
        sys.exit(1)

    new_title = " ".join(new_title_parts)
    record_undo(tasks, next_id)
    tasks[key]["title"] = new_title
    save_tasks(tasks, next_id)
    print("Edited {}".format(task_id))


def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks.values() if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])
    if not matches:
        print("No matches")
        return
    for t in matches:
        print(format_task(t))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing value for --format", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            print("Unknown option: {}".format(args[i]), file=sys.stderr)
            sys.exit(1)

    if fmt is None:
        print("Missing --format", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load_tasks()
    task_list = sorted(tasks.values(), key=lambda t: t["id"])

    if fmt == "json":
        output = []
        for t in task_list:
            output.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(output))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in task_list:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print("{},{},{},{},{},{}".format(
                t["id"], t["title"], done_str,
                t.get("priority", "medium"), tags_str, due_str))
    else:
        print("Unknown format: {}".format(fmt), file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total))


def cmd_undo(args):
    undo_last()


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


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
