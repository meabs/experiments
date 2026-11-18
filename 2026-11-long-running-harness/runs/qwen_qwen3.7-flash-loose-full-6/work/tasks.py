#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, date

DATA_FILE = "tasks.json"
UNDO_FILE = "undo.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        tasks = {int(k): v for k, v in data["tasks"].items()}
        return tasks, data["next_id"]
    except (json.JSONDecodeError, KeyError):
        return {}, 1


def save_tasks(tasks, next_id):
    str_tasks = {str(k): v for k, v in tasks.items()}
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": str_tasks, "next_id": next_id}, f)


def load_undo():
    if not os.path.exists(UNDO_FILE):
        return []
    try:
        with open(UNDO_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_undo(history):
    with open(UNDO_FILE, "w") as f:
        json.dump(history, f)


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = str(task["id"]) + " " + status + " " + task["title"]
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        line += " " + " ".join("#" + t for t in task["tags"])
    if task.get("due"):
        line += " due:" + task["due"]
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def push_undo(command_type, task_id=None, old_task=None, new_task=None, old_next_id=None):
    history = load_undo()
    entry = {"type": command_type}
    if task_id is not None:
        entry["task_id"] = task_id
    if old_task is not None:
        entry["old_task"] = old_task
    if new_task is not None:
        entry["new_task"] = new_task
    if old_next_id is not None:
        entry["old_next_id"] = old_next_id
    history.append(entry)
    save_undo(history)


def do_add(argv):
    title = None
    priority = "medium"
    tags = []
    due = None

    i = 0
    while i < len(argv):
        if argv[i] == "--priority":
            if i + 1 >= len(argv):
                error("Invalid priority: ")
            priority = argv[i + 1]
            if priority not in ("high", "medium", "low"):
                error(f"Invalid priority: {priority}")
            i += 2
        elif argv[i] == "--tag":
            if i + 1 >= len(argv):
                error("Missing tag value")
            tags.append(argv[i + 1])
            i += 2
        elif argv[i] == "--due":
            if i + 1 >= len(argv):
                error("Missing due date")
            due = argv[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                error(f"Invalid date: {due}")
            i += 2
        else:
            if title is None:
                title = argv[i]
            i += 1

    if title is None:
        error("Usage: add TITLE")

    tasks, next_id = load_tasks()
    push_undo("add", task_id=next_id, old_next_id=next_id)

    task = {
        "id": next_id,
        "title": title,
        "done": False,
        "priority": priority,
        "tags": tags,
        "due": due,
    }
    tasks[next_id] = task
    save_tasks(tasks, next_id + 1)
    print(f"Added {next_id}")


def do_list(argv):
    sort_priority = False
    filter_tag = None
    overdue = False
    today_str = None

    i = 0
    while i < len(argv):
        if argv[i] == "--sort":
            if i + 1 >= len(argv):
                error("Missing sort value")
            if argv[i + 1] == "priority":
                sort_priority = True
            i += 2
        elif argv[i] == "--tag":
            if i + 1 >= len(argv):
                error("Missing tag value")
            filter_tag = argv[i + 1]
            i += 2
        elif argv[i] == "--overdue":
            overdue = True
            i += 1
        elif argv[i] == "--today":
            if i + 1 >= len(argv):
                error("Missing today date")
            today_str = argv[i + 1]
            i += 2
        else:
            i += 1

    tasks, _ = load_tasks()

    if overdue:
        if today_str is None:
            today_str = date.today().isoformat()
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        except ValueError:
            error(f"Invalid date: {today_str}")

    result = []
    for tid in sorted(tasks.keys()):
        task = tasks[tid]
        if filter_tag is not None:
            if filter_tag not in task.get("tags", []):
                continue
        if overdue:
            if task["done"]:
                continue
            if task.get("due"):
                try:
                    due_date = datetime.strptime(task["due"], "%Y-%m-%d").date()
                    if due_date >= today_date:
                        continue
                except ValueError:
                    continue
            else:
                continue
        result.append(task)

    if sort_priority:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        result.sort(key=lambda t: t["id"])

    if not result:
        print("No tasks")
    else:
        for task in result:
            print(task_line(task))


def do_done(argv):
    if not argv:
        error("Usage: done ID")
    task_id = int(argv[0])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        error(f"No such task: {task_id}")
    push_undo("done", task_id=task_id, old_task=dict(tasks[task_id]))
    tasks[task_id]["done"] = True
    save_tasks(tasks, next_id)
    print(f"Done {task_id}")


def do_delete(argv):
    if not argv:
        error("Usage: delete ID")
    task_id = int(argv[0])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        error(f"No such task: {task_id}")
    push_undo("delete", task_id=task_id, old_task=dict(tasks[task_id]), old_next_id=next_id)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    print(f"Deleted {task_id}")


def do_edit(argv):
    if not argv:
        error("Usage: edit ID --title ...")
    task_id = int(argv[0])
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        error(f"No such task: {task_id}")

    new_title = None
    i = 1
    while i < len(argv):
        if argv[i] == "--title":
            if i + 1 >= len(argv):
                error("Missing title value")
            new_title = argv[i + 1]
            i += 2
        else:
            i += 1

    if new_title is None:
        error("Usage: edit ID --title NEW TITLE")

    push_undo("edit", task_id=task_id, old_task=dict(tasks[task_id]))
    tasks[task_id]["title"] = new_title
    save_tasks(tasks, next_id)
    print(f"Edited {task_id}")


def do_search(argv):
    if not argv:
        error("Usage: search TEXT")
    query = argv[0].lower()
    tasks, _ = load_tasks()
    results = []
    for tid in sorted(tasks.keys()):
        task = tasks[tid]
        if query in task["title"].lower():
            results.append(task)
    if not results:
        print("No matches")
    else:
        for task in results:
            print(task_line(task))


def do_export(argv):
    fmt = None
    i = 0
    while i < len(argv):
        if argv[i] == "--format":
            if i + 1 >= len(argv):
                error("Missing format value")
            fmt = argv[i + 1]
            i += 2
        else:
            i += 1

    if fmt is None or fmt not in ("json", "csv"):
        error("Usage: export --format json|csv")

    tasks, _ = load_tasks()
    result = []
    for tid in sorted(tasks.keys()):
        task = tasks[tid]
        result.append({
            "id": task["id"],
            "title": task["title"],
            "done": task["done"],
            "priority": task.get("priority", "medium"),
            "tags": task.get("tags", []),
            "due": task.get("due"),
        })

    if fmt == "json":
        print(json.dumps(result, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for item in result:
            tags_str = ";".join(item["tags"]) if item["tags"] else ""
            print(f"{item['id']},{item['title']},{str(item['done']).lower()},{item['priority']},{tags_str},{item['due'] or ''}")


def do_stats(argv):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t["done"])
    done_count = sum(1 for t in tasks.values() if t["done"])
    total = len(tasks)
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def do_undo(argv):
    history = load_undo()
    if not history:
        error("Nothing to undo")

    last = history.pop()
    save_undo(history)

    tasks, next_id = load_tasks()

    if last["type"] == "add":
        task_id = last["task_id"]
        if task_id in tasks:
            del tasks[task_id]
        save_tasks(tasks, last["old_next_id"])
    elif last["type"] == "done":
        task_id = last["task_id"]
        if task_id in tasks:
            tasks[task_id] = last["old_task"]
        save_tasks(tasks, next_id)
    elif last["type"] == "delete":
        task_id = last["task_id"]
        tasks[task_id] = last["old_task"]
        save_tasks(tasks, last["old_next_id"])
    elif last["type"] == "edit":
        task_id = last["task_id"]
        if task_id in tasks:
            tasks[task_id] = last["old_task"]
        save_tasks(tasks, next_id)

    print("Undone")


def main():
    cmd, args = parse_args(sys.argv[1:])
    commands = {
        "add": do_add,
        "list": do_list,
        "done": do_done,
        "delete": do_delete,
        "edit": do_edit,
        "search": do_search,
        "export": do_export,
        "stats": do_stats,
        "undo": do_undo,
    }
    handler = commands.get(cmd)
    if handler is None:
        error(f"Unknown command: {cmd}")
    handler(args)


def parse_args(argv):
    if not argv:
        print("Usage: python3 tasks.py <command> [args]", file=sys.stderr)
        sys.exit(1)
    return argv[0], argv[1:]


if __name__ == "__main__":
    main()
