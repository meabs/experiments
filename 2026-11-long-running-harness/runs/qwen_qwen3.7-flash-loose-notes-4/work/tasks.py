#!/usr/bin/env python3
"""Command-line task manager."""
import json, os, sys
from datetime import date, datetime

DATA_FILE = "tasks.json"
HISTORY_FILE = "_history.json"

def load_tasks():
    if not os.path.exists(DATA_FILE): return [], 1
    with open(DATA_FILE) as f: data = json.load(f)
    return data.get("tasks", []), data.get("next_id", 1)

def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f: json.dump({"tasks": tasks, "next_id": next_id}, f)

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE) as f: return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f: json.dump(history, f)

def fmt(task):
    s = "[x]" if task["done"] else "[ ]"
    p = [f'{task["id"]} {s} {task["title"]}']
    if task.get("priority") == "high": p.append("(high)")
    elif task.get("priority") == "low": p.append("(low)")
    if task.get("tags"): p.append(" ".join(f"#{t}" for t in task["tags"]))
    if task.get("due"): p.append(f"due:{task['due']}")
    return " ".join(p)

def cmd_add(args):
    title_parts, priority, tags, due = [], None, [], None
    i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i+1>=len(args): print("Missing value for --priority",file=sys.stderr); sys.exit(1)
            priority = args[i+1]
            if priority not in ("high","medium","low"): print(f"Invalid priority: {priority}",file=sys.stderr); sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i+1>=len(args): print("Missing value for --tag",file=sys.stderr); sys.exit(1)
            tags.append(args[i+1]); i += 2
        elif args[i] == "--due":
            if i+1>=len(args): print("Missing value for --due",file=sys.stderr); sys.exit(1)
            due = args[i+1]
            try: datetime.strptime(due,"%Y-%m-%d")
            except ValueError: print(f"Invalid date: {due}",file=sys.stderr); sys.exit(1)
            i += 2
        else: title_parts.append(args[i]); i += 1
    if not title_parts: print("Usage: add TITLE [--priority ...] [--tag TAG]... [--due YYYY-MM-DD]",file=sys.stderr); sys.exit(1)
    title = " ".join(title_parts)
    tasks, next_id = load_tasks()
    task = {"id":next_id,"title":title,"done":False,"priority":priority or "medium","tags":tags,"due":due}
    tasks.append(task)
    history = load_history()
    history.append({"action":"add","task":task,"old_next_id":next_id})
    save_history(history)
    save_tasks(tasks, next_id+1)
    print(f"Added {next_id}")

def cmd_list(args):
    tasks, _ = load_tasks()
    sort_pri, filter_tag, overdue, today_str = False, None, False, None
    i = 0
    while i < len(args):
        if args[i] == "--sort":
            if i+1>=len(args): print("Missing value for --sort",file=sys.stderr); sys.exit(1)
            if args[i+1]!="priority": print(f"Unknown sort option: {args[i+1]}",file=sys.stderr); sys.exit(1)
            sort_pri=True; i+=2
        elif args[i]=="--tag":
            if i+1>=len(args): print("Missing value for --tag",file=sys.stderr); sys.exit(1)
            filter_tag=args[i+1]; i+=2
        elif args[i]=="--overdue": overdue=True; i+=1
        elif args[i]=="--today":
            if i+1>=len(args): print("Missing value for --today",file=sys.stderr); sys.exit(1)
            today_str=args[i+1]
            try: datetime.strptime(today_str,"%Y-%m-%d")
            except ValueError: print(f"Invalid date: {today_str}",file=sys.stderr); sys.exit(1)
            i+=2
        else: i+=1
    if today_str is None: today_str=date.today().isoformat()
    today=date.fromisoformat(today_str)
    if filter_tag is not None: tasks=[t for t in tasks if filter_tag in t.get("tags",[])]
    if overdue:
        filtered=[]
        for t in tasks:
            if t["done"]: continue
            if t.get("due") and t["due"]<today_str: filtered.append(t)
        tasks=filtered
    if sort_pri:
        po={"high":0,"medium":1,"low":2}
        tasks=sorted(tasks,key=lambda t:(po.get(t.get("priority","medium"),1),t["id"]))
    else: tasks=sorted(tasks,key=lambda t:t["id"])
    if not tasks: print("No tasks"); return
    for task in tasks: print(fmt(task))

def cmd_done(args):
    if not args: print("Usage: done ID",file=sys.stderr); sys.exit(1)
    try: task_id=int(args[0])
    except ValueError: print(f"Invalid id: {args[0]}",file=sys.stderr); sys.exit(1)
    tasks,next_id=load_tasks()
    found=None
    for t in tasks:
        if t["id"]==task_id: found=t; break
    if found is None: print(f"No such task: {task_id}",file=sys.stderr); sys.exit(1)
    found["done"]=True
    history=load_history(); history.append({"action":"done","task_id":task_id,"old_done":False})
    save_history(history); save_tasks(tasks,next_id)
    print(f"Done {task_id}")

def cmd_delete(args):
    if not args: print("Usage: delete ID",file=sys.stderr); sys.exit(1)
    try: task_id=int(args[0])
    except ValueError: print(f"Invalid id: {args[0]}",file=sys.stderr); sys.exit(1)
    tasks,next_id=load_tasks()
    found=None
    for t in tasks:
        if t["id"]==task_id: found=t; break
    if found is None: print(f"No such task: {task_id}",file=sys.stderr); sys.exit(1)
    tasks=[t for t in tasks if t["id"]!=task_id]
    history=load_history(); history.append({"action":"delete","task":found,"old_next_id":next_id})
    save_history(history); save_tasks(tasks,next_id)
    print(f"Deleted {task_id}")

def cmd_edit(args):
    if not args: print("Usage: edit ID --title NEW TITLE",file=sys.stderr); sys.exit(1)
    try: task_id=int(args[0])
    except ValueError: print(f"Invalid id: {args[0]}",file=sys.stderr); sys.exit(1)
    tasks,next_id=load_tasks()
    found=None
    for t in tasks:
        if t["id"]==task_id: found=t; break
    if found is None: print(f"No such task: {task_id}",file=sys.stderr); sys.exit(1)
    ts=None
    for idx,arg in enumerate(args):
        if arg=="--title":
            if idx+1>=len(args): print("Missing value for --title",file=sys.stderr); sys.exit(1)
            ts=idx+1; break
    if ts is None: print("Usage: edit ID --title NEW TITLE",file=sys.stderr); sys.exit(1)
    new_title=" ".join(args[ts:])
    old_title=found["title"]; found["title"]=new_title
    history=load_history(); history.append({"action":"edit","task_id":task_id,"old_title":old_title})
    save_history(history); save_tasks(tasks,next_id)
    print(f"Edited {task_id}")

def cmd_search(args):
    if not args: print("Usage: search TEXT",file=sys.stderr); sys.exit(1)
    query=" ".join(args).lower()
    tasks,_=load_tasks()
    matches=[t for t in tasks if query in t["title"].lower()]
    matches.sort(key=lambda t:t["id"])
    if not matches: print("No matches"); return
    for task in matches: print(fmt(task))

def cmd_export(args):
    fmt_type=None; i=0
    while i<len(args):
        if args[i]=="--format":
            if i+1>=len(args): print("Missing value for --format",file=sys.stderr); sys.exit(1)
            fmt_type=args[i+1]
            if fmt_type not in ("json","csv"): print(f"Unknown format: {fmt_type}",file=sys.stderr); sys.exit(1)
            i+=2
        else: i+=1
    if fmt_type is None: print("Usage: export --format json|csv",file=sys.stderr); sys.exit(1)
    tasks,_=load_tasks(); tasks.sort(key=lambda t:t["id"])
    if fmt_type=="json":
        out=[]
        for t in tasks: out.append({"id":t["id"],"title":t["title"],"done":t["done"],"priority":t["priority"],"tags":t["tags"],"due":t.get("due")})
        print(json.dumps(out))
    elif fmt_type=="csv":
        lines=["id,title,done,priority,tags,due"]
        for t in tasks:
            lines.append(f"{t['id']},{t['title']},{'true' if t['done'] else 'false'},{t['priority']},{';'.join(t.get('tags',[]))},{t.get('due') or ''}")
        print("\n".join(lines))

def cmd_stats(args):
    tasks,_=load_tasks()
    oc=sum(1 for t in tasks if not t["done"])
    dc=sum(1 for t in tasks if t["done"])
    print(f"open: {oc}\ndone: {dc}\ntotal: {len(tasks)}")

def cmd_undo(args):
    history=load_history()
    if not history: print("Nothing to undo",file=sys.stderr); sys.exit(1)
    entry=history.pop(); tasks,next_id=load_tasks(); action=entry["action"]
    if action=="add":
        tasks=[t for t in tasks if t["id"]!=entry["task"]["id"]]
        next_id=entry["old_next_id"]
    elif action=="delete":
        tasks.append(entry["task"])
    elif action=="done":
        found=None
        for t in tasks:
            if t["id"]==entry["task_id"]: found=t; break
        if found: found["done"]=entry["old_done"]
    elif action=="edit":
        found=None
        for t in tasks:
            if t["id"]==entry["task_id"]: found=t; break
        if found: found["title"]=entry["old_title"]
    save_history(history); save_tasks(tasks,next_id)
    print("Undone")

if __name__=="__main__":
    if len(sys.argv)<2: print("Usage: python3 tasks.py <command> [args]",file=sys.stderr); sys.exit(1)
    cmds={"add":cmd_add,"list":cmd_list,"done":cmd_done,"delete":cmd_delete,"edit":cmd_edit,"search":cmd_search,"export":cmd_export,"stats":cmd_stats,"undo":cmd_undo}
    cmd=sys.argv[1]
    if cmd not in cmds: print(f"Unknown command: {cmd}",file=sys.stderr); sys.exit(1)
    cmds[cmd](sys.argv[2:])
