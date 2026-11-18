#!/usr/bin/env python3
"""Command-line task manager."""

import json, sys, os
from datetime import date, datetime

DATA_FILE = "tasks.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

def push_undo(data):
    data["undo_history"].append({
        "tasks": [dict(t) for t in data["tasks"]],
        "next_id": data["next_id"],
    })

def fmt(task):
    s = "[x]" if task["done"] else "[ ]"
    l = f"{task['id']} {s} {task['title']}"
    if task.get("priority") == "high": l += " (high)"
    elif task.get("priority") == "low": l += " (low)"
    tags = task.get("tags", [])
    if tags: l += " " + " ".join(f"#{t}" for t in tags)
    d = task.get("due")
    if d: l += f" due:{d}"
    return l

def cmd_add(args, data):
    if not args:
        print("Usage: add TITLE", file=sys.stderr); sys.exit(1)
    title_parts = []; priority = None; tags = []; due = None; i = 0
    while i < len(args):
        a = args[i]
        if a == "--priority":
            if i+1 >= len(args): print("Missing --priority value",file=sys.stderr); sys.exit(1)
            priority = args[i+1]
            if priority not in ("high","medium","low"): print(f"Invalid priority: {priority}",file=sys.stderr); sys.exit(1)
            i += 2
        elif a == "--tag":
            if i+1 >= len(args): print("Missing --tag value",file=sys.stderr); sys.exit(1)
            tags.append(args[i+1]); i += 2
        elif a == "--due":
            if i+1 >= len(args): print("Missing --due value",file=sys.stderr); sys.exit(1)
            ds = args[i+1]
            try: datetime.strptime(ds, "%Y-%m-%d")
            except ValueError: print(f"Invalid date: {ds}",file=sys.stderr); sys.exit(1)
            due = ds; i += 2
        else: title_parts.append(a); i += 1
    push_undo(data)
    task = {"id": data["next_id"], "title": " ".join(title_parts), "done": False,
            "priority": priority or "medium", "tags": tags, "due": due}
    data["tasks"].append(task); data["next_id"] += 1
    save_data(data); print(f"Added {task['id']}")

def cmd_list(args, data):
    sort_p = False; tag_f = None; overdue = False; today_s = None; i = 0
    while i < len(args):
        a = args[i]
        if a == "--sort":
            if i+1 >= len(args): print("Missing --sort value",file=sys.stderr); sys.exit(1)
            if args[i+1] != "priority": print(f"Invalid sort: {args[i+1]}",file=sys.stderr); sys.exit(1)
            sort_p = True; i += 2
        elif a == "--tag":
            if i+1 >= len(args): print("Missing --tag value",file=sys.stderr); sys.exit(1)
            tag_f = args[i+1]; i += 2
        elif a == "--overdue": overdue = True; i += 1
        elif a == "--today":
            if i+1 >= len(args): print("Missing --today value",file=sys.stderr); sys.exit(1)
            today_s = args[i+1]
            try: datetime.strptime(today_s, "%Y-%m-%d")
            except ValueError: print(f"Invalid date: {today_s}",file=sys.stderr); sys.exit(1)
            i += 2
        else: print(f"Unknown option: {a}",file=sys.stderr); sys.exit(1)
    tasks = list(data["tasks"])
    if tag_f: tasks = [t for t in tasks if tag_f in t.get("tags",[])]
    if overdue:
        td = datetime.strptime(today_s, "%Y-%m-%d").date() if today_s else date.today()
        tasks = [t for t in tasks if not t["done"] and t.get("due") and datetime.strptime(t["due"],"%Y-%m-%d").date() < td]
    if sort_p:
        po = {"high":0,"medium":1,"low":2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get("priority","medium"),1), t["id"]))
    else: tasks = sorted(tasks, key=lambda t: t["id"])
    if not tasks: print("No tasks")
    else:
        for task in tasks: print(fmt(task))

def cmd_done(args, data):
    if not args: print("Usage: done ID",file=sys.stderr); sys.exit(1)
    try: tid = int(args[0])
    except ValueError: print(f"Invalid id: {args[0]}",file=sys.stderr); sys.exit(1)
    task = next((t for t in data["tasks"] if t["id"]==tid), None)
    if task is None: print(f"No such task: {tid}",file=sys.stderr); sys.exit(1)
    push_undo(data); task["done"] = True; save_data(data); print(f"Done {tid}")

def cmd_delete(args, data):
    if not args: print("Usage: delete ID",file=sys.stderr); sys.exit(1)
    try: tid = int(args[0])
    except ValueError: print(f"Invalid id: {args[0]}",file=sys.stderr); sys.exit(1)
    ti = None
    for i,t in enumerate(data["tasks"]):
        if t["id"]==tid: ti=i; break
    if ti is None: print(f"No such task: {tid}",file=sys.stderr); sys.exit(1)
    push_undo(data); data["tasks"].pop(ti); save_data(data); print(f"Deleted {tid}")

def cmd_edit(args, data):
    if not args: print("Usage: edit ID --title NEW TITLE",file=sys.stderr); sys.exit(1)
    try: tid = int(args[0])
    except ValueError: print(f"Invalid id: {args[0]}",file=sys.stderr); sys.exit(1)
    task = next((t for t in data["tasks"] if t["id"]==tid), None)
    if task is None: print(f"No such task: {tid}",file=sys.stderr); sys.exit(1)
    idx = next((i for i,a in enumerate(args) if a=="--title"), None)
    if idx is None or idx+1 >= len(args): print("Usage: edit ID --title NEW TITLE",file=sys.stderr); sys.exit(1)
    tp = args[idx+1:]
    push_undo(data); task["title"] = " ".join(tp); save_data(data); print(f"Edited {tid}")

def cmd_search(args, data):
    if not args: print("Usage: search TEXT",file=sys.stderr); sys.exit(1)
    q = " ".join(args).lower()
    m = sorted([t for t in data["tasks"] if q in t["title"].lower()], key=lambda t: t["id"])
    if not m: print("No matches")
    else:
        for task in m: print(fmt(task))

def cmd_export(args, data):
    fmt_name = None; i = 0
    while i < len(args):
        if args[i] == "--format":
            if i+1 >= len(args): print("Missing --format value",file=sys.stderr); sys.exit(1)
            fmt_name = args[i+1]
            if fmt_name not in ("json","csv"): print(f"Invalid format: {fmt_name}",file=sys.stderr); sys.exit(1)
            i += 2
        else: print(f"Unknown option: {args[i]}",file=sys.stderr); sys.exit(1)
    if fmt_name is None: print("Usage: export --format json|csv",file=sys.stderr); sys.exit(1)
    tasks = sorted(data["tasks"], key=lambda t: t["id"])
    if fmt_name == "json":
        out = [{"id":t["id"],"title":t["title"],"done":t["done"],"priority":t.get("priority","medium"),"tags":t.get("tags",[]),"due":t.get("due")} for t in tasks]
        print(json.dumps(out, indent=2))
    elif fmt_name == "csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            ts = ";".join(t.get("tags",[])); ds = t.get('due') or ''
            print(f"{t['id']},{t['title']},{str(t['done']).lower()},{t.get('priority','medium')},{ts},{ds}")

def cmd_stats(args, data):
    oc = sum(1 for t in data["tasks"] if not t["done"])
    dc = sum(1 for t in data["tasks"] if t["done"])
    print(f"open: {oc}\ndone: {dc}\ntotal: {len(data['tasks'])}")

def cmd_undo(args, data):
    if not data["undo_history"]: print("Nothing to undo",file=sys.stderr); sys.exit(1)
    snap = data["undo_history"].pop()
    data["tasks"] = snap["tasks"]; data["next_id"] = snap["next_id"]
    save_data(data); print("Undone")

CMDS = {"add":cmd_add,"list":cmd_list,"done":cmd_done,"delete":cmd_delete,
        "edit":cmd_edit,"search":cmd_search,"export":cmd_export,
        "stats":cmd_stats,"undo":cmd_undo}

def main():
    if len(sys.argv) < 2: print("Usage: python3 tasks.py <command> [args]",file=sys.stderr); sys.exit(1)
    cmd = sys.argv[1]; args = sys.argv[2:]
    if cmd not in CMDS: print(f"Unknown command: {cmd}",file=sys.stderr); sys.exit(1)
    data = load_data(); CMDS[cmd](args, data)

if __name__ == "__main__":
    main()
