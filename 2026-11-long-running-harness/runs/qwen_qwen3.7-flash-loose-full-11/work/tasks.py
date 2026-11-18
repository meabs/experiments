#!/usr/bin/env python3
import json, os, sys
from datetime import date

DATA_FILE = "tasks.json"
HISTORY_FILE = "history.json"

def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        return data.get("tasks", []), data.get("next_id", 1)
    except (json.JSONDecodeError, KeyError):
        return [], 1

def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError):
        return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def push_undo(tasks, next_id):
    history = load_history()
    history.append({"tasks": tasks, "next_id": next_id})
    save_history(history)

def undo_last():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = history.pop()
    save_history(history)
    save_tasks(state["tasks"], state["next_id"])
    print("Undone")

def task_line(task):
    done_mark = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], done_mark, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    if tags:
        tag_str = " ".join("#{}".format(t) for t in tags)
        line += " " + tag_str
    due = task.get("due", None)
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
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("Invalid priority: ", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("Missing due date", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Missing task title", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)
    if priority not in ("high", "medium", "low"):
        print("Invalid priority: {}".format(priority), file=sys.stderr)
        sys.exit(1)
    if due is not None:
        try:
            parts = due.split("-")
            if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                raise ValueError
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            date(y, m, d)
        except (ValueError, IndexError):
            print("Invalid date: {}".format(due), file=sys.stderr)
            sys.exit(1)
    return title, priority, tags, due

def cmd_add(args):
    if not args:
        print("Usage: add TITLE", file=sys.stderr)
        sys.exit(1)
    title, priority, tags, due = parse_add_args(args)
    tasks, next_id = load_tasks()
    push_undo(tasks, next_id)
    task = {"id": next_id, "title": title, "done": False, "priority": priority, "tags": tags, "due": due}
    tasks.append(task)
    save_tasks(tasks, next_id + 1)
    print("Added {}".format(next_id))

def cmd_list(args):
    tasks, _ = load_tasks()
    sort_mode = None
    tag_filter = None
    overdue = False
    today = None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i + 1 >= len(args):
                print("Missing sort value", file=sys.stderr)
                sys.exit(1)
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("Missing tag value", file=sys.stderr)
                sys.exit(1)
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today":
            if i + 1 >= len(args):
                print("Missing date value", file=sys.stderr)
                sys.exit(1)
            today = args[i + 1]
            i += 2
        else:
            i += 1
    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]
    if overdue:
        if today is None:
            today_str = date.today().isoformat()
        else:
            today_str = today
        try:
            date.fromisoformat(today_str)
        except ValueError:
            print("Invalid date: {}".format(today_str), file=sys.stderr)
            sys.exit(1)
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] < today_str]
    if sort_mode == "priority":
        porder = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda t: (porder.get(t.get("priority", "medium"), 1), t["id"]))
    if not tasks:
        print("No tasks")
        return
    for task in tasks:
        print(task_line(task))

def cmd_done(args):
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            push_undo(tasks, next_id)
            task["done"] = True
            save_tasks(tasks, next_id)
            print("Done {}".format(task_id))
            return
    print("No such task: {}".format(task_id), file=sys.stderr)
    sys.exit(1)

def cmd_delete(args):
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print("No such task: {}".format(task_id), file=sys.stderr)
        sys.exit(1)
    push_undo(tasks, next_id)
    save_tasks(new_tasks, next_id)
    print("Deleted {}".format(task_id))

def cmd_edit(args):
    if not args:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print("No such task: {}".format(args[0]), file=sys.stderr)
        sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == "--title":
            if i + 1 >= len(args):
                print("Missing title", file=sys.stderr)
                sys.exit(1)
            title_parts = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                title_parts.append(args[i])
                i += 1
            new_title = " ".join(title_parts)
        else:
            i += 1
    if new_title is None:
        print("Missing --title", file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            push_undo(tasks, next_id)
            task["title"] = new_title
            save_tasks(tasks, next_id)
            print("Edited {}".format(task_id))
            return
    print("No such task: {}".format(task_id), file=sys.stderr)
    sys.exit(1)

def cmd_search(args):
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    search_text = " ".join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks if search_text in t["title"].lower()]
    if not matches:
        print("No matches")
        return
    for task in sorted(matches, key=lambda t: t["id"]):
        print(task_line(task))

def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format":
            if i + 1 >= len(args):
                print("Missing format value", file=sys.stderr)
                sys.exit(1)
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if fmt is None:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)
    tasks, _ = load_tasks()
    tasks = sorted(tasks, key=lambda t: t["id"])
    if fmt == "json":
        output = []
        for t in tasks:
            output.append({"id": t["id"], "title": t["title"], "done": t["done"], "priority": t.get("priority", "medium"), "tags": t.get("tags", []), "due": t.get("due", None)})
        print(json.dumps(output, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            done_str = "true" if t["done"] else "false"
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due", "")
            row = "{},{},{},{},{},{}".format(t["id"], t["title"], done_str, t.get("priority", "medium"), tags_str, due_str)
            print(row)

def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks if not t["done"])
    done_count = sum(1 for t in tasks if t["done"])
    total_count = len(tasks)
    print("open: {}".format(open_count))
    print("done: {}".format(done_count))
    print("total: {}".format(total_count))

COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "delete": cmd_delete,
    "edit": cmd_edit,
    "search": cmd_search,
    "export": cmd_export,
    "stats": cmd_stats,
    "undo": lambda a: undo_last(),
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    handler = COMMANDS.get(command)
    if handler is None:
        print("Unknown command: {}".format(command), file=sys.stderr)
        sys.exit(1)
    handler(sys.argv[2:])
