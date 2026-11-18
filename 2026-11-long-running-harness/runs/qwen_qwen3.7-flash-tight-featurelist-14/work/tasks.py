#!/usr/bin/env python3
"""A command-line task manager."""
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"


def load():
    """Load tasks and undo history from disk."""
    if not os.path.exists(DATA_FILE):
        return [], []
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get("tasks", []), data.get("history", [])


def save(tasks, history):
    """Save tasks and undo history to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "history": history}, f)


def next_id(tasks):
    """Compute the next task id (max existing + 1, or 1)."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def task_line(task):
    """Format a task as its display line."""
    status = "[x]" if task["done"] else "[ ]"
    parts = [str(task["id"]), status, task["title"]]
    # Priority suffix
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    # Tags suffix
    if task.get("tags"):
        parts.extend(task["tags"])
    # Due date suffix
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def cmd_add(args):
    """Handle 'add' command."""
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i + 1 >= len(args):
                print("--priority requires a value", file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if priority not in ("high", "medium", "low"):
                print(f"Invalid priority: {priority}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i + 1 >= len(args):
                print("--tag requires a value", file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == "--due":
            if i + 1 >= len(args):
                print("--due requires a value", file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: {due}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    if not title_parts:
        print("Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]", file=sys.stderr)
        sys.exit(1)
    title = " ".join(title_parts)

    tasks, history = load()
    tid = next_id(tasks)
    task = {
        "id": tid,
        "title": title,
        "done": False,
        "priority": priority or "medium",
        "tags": tags,
        "due": due,
    }
    # Save state before mutation for undo
    history.append({"tasks": json.loads(json.dumps(tasks)), "next_id": tid})
    tasks.append(task)
    save(tasks, history)
    print(f"Added {tid}")


def cmd_list(args):
    """Handle 'list' command."""
    tasks, _ = load()
    sort_mode = None
    tag_filter = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            sort_mode = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == "--overdue":
            overdue = True
            i += 1
        elif args[i] == "--today" and i + 1 < len(args):
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1

    if overdue:
        if today_arg:
            try:
                today = datetime.strptime(today_arg, "%Y-%m-%d").date()
            except ValueError:
                print(f"Invalid date: {today_arg}", file=sys.stderr)
                sys.exit(1)
        else:
            today = date.today()
        filtered = []
        for t in tasks:
            if t["done"]:
                continue
            if t.get("due"):
                try:
                    d = datetime.strptime(t["due"], "%Y-%m-%d").date()
                    if d < today:
                        filtered.append(t)
                except ValueError:
                    pass
        tasks = filtered

    if tag_filter:
        tasks = [t for t in tasks if tag_filter in t.get("tags", [])]

    if sort_mode == "priority":
        prio_order = {"high": 0, "medium": 1, "low": 2}
        tasks = sorted(tasks, key=lambda t: (prio_order.get(t.get("priority", "medium"), 1), t["id"]))
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])

    if not tasks:
        print("No tasks")
        return

    for t in tasks:
        print(task_line(t))


def cmd_done(args):
    """Handle 'done' command."""
    if not args:
        print("Usage: done ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, history = load()
    found = False
    for t in tasks:
        if t["id"] == tid:
            t["done"] = True
            history.append({"tasks": json.loads(json.dumps(tasks)), "next_id": next_id(tasks)})
            save(tasks, history)
            print(f"Done {tid}")
            found = True
            break
    if not found:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    """Handle 'delete' command."""
    if not args:
        print("Usage: delete ID", file=sys.stderr)
        sys.exit(1)
    try:
        tid = int(args[0])
    except ValueError:
        print(f"No such task: {args[0]}", file=sys.stderr)
        sys.exit(1)

    tasks, history = load()
    found = False
    for t in tasks:
        if t["id"] == tid:
            tasks.remove(t)
            history.append({"tasks": json.loads(json.dumps(tasks)), "next_id": next_id(tasks)})
            save(tasks, history)
            print(f"Deleted {tid}")
            found = True
            break
    if not found:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)


def cmd_edit(args):
    """Handle 'edit' command."""
    new_title = None
    i = 0
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            new_title = args[i + 1:]
            i += 2
        else:
            i += 1

    if not new_title:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    if not args[:i] or args[:i][0].isdigit():
        try:
            tid = int(args[0])
        except (ValueError, IndexError):
            print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: edit ID --title NEW TITLE", file=sys.stderr)
        sys.exit(1)

    tasks, history = load()
    found = False
    for t in tasks:
        if t["id"] == tid:
            t["title"] = " ".join(new_title)
            history.append({"tasks": json.loads(json.dumps(tasks)), "next_id": next_id(tasks)})
            save(tasks, history)
            print(f"Edited {tid}")
            found = True
            break
    if not found:
        print(f"No such task: {tid}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args):
    """Handle 'search' command."""
    if not args:
        print("Usage: search TEXT", file=sys.stderr)
        sys.exit(1)
    query = " ".join(args).lower()

    tasks, _ = load()
    matches = [t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t: t["id"])

    if not matches:
        print("No matches")
        return

    for t in matches:
        print(task_line(t))


def cmd_export(args):
    """Handle 'export' command."""
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    if not fmt:
        print("Usage: export --format json|csv", file=sys.stderr)
        sys.exit(1)

    tasks, _ = load()
    tasks = sorted(tasks, key=lambda t: t["id"])

    if fmt == "json":
        out = []
        for t in tasks:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "done": t["done"],
                "priority": t.get("priority", "medium"),
                "tags": t.get("tags", []),
                "due": t.get("due"),
            })
        print(json.dumps(out, indent=2))
    elif fmt == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            tags_str = ";".join(t.get("tags", []))
            due_str = t.get("due") or ""
            print(f"{t['id']},{t['title']},{str(t['done']).lower()},{t.get('priority','medium')},{tags_str},{due_str}")
    else:
        print(f"Invalid format: {fmt}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Handle 'stats' command."""
    tasks, _ = load()
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    print(f"open: {open_count}")
    print(f"done: {done_count}")
    print(f"total: {total}")


def cmd_undo(args):
    """Handle 'undo' command."""
    tasks, history = load()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    prev = history.pop()
    save(prev["tasks"], history)
    print("Undone")


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
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: tasks.py <command> [args]", file=sys.stderr)
        print(f"Commands: {', '.join(COMMANDS.keys())}", file=sys.stderr)
        sys.exit(1)
    cmd_name = sys.argv[1]
    COMMANDS[cmd_name](sys.argv[2:])


if __name__ == "__main__":
    main()
