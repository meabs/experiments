#!/usr/bin/env python3
import json, os, sys
from datetime import date

DATA_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "undo_stack": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def task_line(task):
    prefix = "[x]" if task["done"] else "[ ]"
    suffixes = ""
    if task.get("priority") == "high":
        suffixes += " (high)"
    elif task.get("priority") == "low":
        suffixes += " (low)"
    if task.get("tags"):
        tag_str = " ".join("#" + t for t in task["tags"])
        suffixes += " " + tag_str
    if task.get("due"):
        suffixes += " due:" + task["due"]
    return "{} {} {}{}".format(task["id"], prefix, task["title"], suffixes)

def cmd_add(args, data):
    title = None; priority = "medium"; tags = []; due = None; i = 0
    while i < len(args):
        if args[i] == "--priority":
            if i+1 >= len(args): print("--priority requires a value", file=sys.stderr); sys.exit(1)
            priority = args[i+1]
            if priority not in ("high","medium","low"): print("Invalid priority: {}".format(priority), file=sys.stderr); sys.exit(1)
            i += 2
        elif args[i] == "--tag":
            if i+1 >= len(args): print("--tag requires a value", file=sys.stderr); sys.exit(1)
            tags.append(args[i+1]); i += 2
        elif args[i] == "--due":
            if i+1 >= len(args): print("--due requires a value", file=sys.stderr); sys.exit(1)
            due = args[i+1]
            try:
                parts = due.split("-")
                if len(parts)!=3 or len(parts[0])!=4 or len(parts[1])!=2 or len(parts[2])!=2: raise ValueError
                y,m,d = int(parts[0]),int(parts[1]),int(parts[2])
                date(y,m,d)
            except (ValueError,IndexError): print("Invalid date: {}".format(due), file=sys.stderr); sys.exit(1)
            i += 2
        else:
            if title is None: title = args[i]
            else: title += " " + args[i]
            i += 1
    if title is None: print("Usage: add TITLE", file=sys.stderr); sys.exit(1)
    task_id = data["next_id"]
    task = {"id":task_id,"title":title,"done":False,"priority":priority,"tags":tags,"due":due}
    data["tasks"].append(task); data["next_id"] += 1
    data["undo_stack"].append({"type":"add","task":task,"prev_next_id":task_id})
    save_tasks(data); print("Added {}".format(task_id))

def cmd_list(args, data):
    sort_by=None; filter_tag=None; overdue=False; today_str=None; i=0
    while i < len(args):
        if args[i]=="--sort":
            if i+1>=len(args): print("--sort requires an argument", file=sys.stderr); sys.exit(1)
            sort_by=args[i+1]; i+=2
        elif args[i]=="--tag":
            if i+1>=len(args): print("--tag requires a value", file=sys.stderr); sys.exit(1)
            filter_tag=args[i+1]; i+=2
        elif args[i]=="--overdue": overdue=True; i+=1
        elif args[i]=="--today":
            if i+1>=len(args): print("--today requires a value", file=sys.stderr); sys.exit(1)
            today_str=args[i+1]; i+=2
        else: i+=1
    tasks=list(data["tasks"])
    if overdue:
        today=date.fromisoformat(today_str) if today_str else date.today()
        tasks=[t for t in tasks if not t["done"] and t.get("due") and t["due"]<today.isoformat()]
    if filter_tag:
        tasks=[t for t in tasks if filter_tag in t.get("tags",[])]
    if sort_by=="priority":
        prio={"high":0,"medium":1,"low":2}
        tasks=sorted(tasks,key=lambda t:(prio.get(t.get("priority","medium"),1),t["id"]))
    elif sort_by: print("Unknown sort option: {}".format(sort_by),file=sys.stderr); sys.exit(1)
    else: tasks=sorted(tasks,key=lambda t:t["id"])
    if not tasks: print("No tasks")
    else:
        for t in tasks: print(task_line(t))

def cmd_done(args, data):
    if not args: print("Usage: done ID",file=sys.stderr); sys.exit(1)
    try: task_id=int(args[0])
    except ValueError: print("Invalid task id: {}".format(args[0]),file=sys.stderr); sys.exit(1)
    for t in data["tasks"]:
        if t["id"]==task_id:
            old_done=t["done"]; t["done"]=True
            data["undo_stack"].append({"type":"done","task_id":task_id,"prev_done":old_done})
            save_tasks(data); print("Done {}".format(task_id)); return
    print("No such task: {}".format(task_id),file=sys.stderr); sys.exit(1)

def cmd_delete(args, data):
    if not args: print("Usage: delete ID",file=sys.stderr); sys.exit(1)
    try: task_id=int(args[0])
    except ValueError: print("Invalid task id: {}".format(args[0]),file=sys.stderr); sys.exit(1)
    for i,t in enumerate(data["tasks"]):
        if t["id"]==task_id:
            deleted=data["tasks"].pop(i)
            data["undo_stack"].append({"type":"delete","task":deleted,"index":i,"prev_next_id":data["next_id"]})
            save_tasks(data); print("Deleted {}".format(task_id)); return
    print("No such task: {}".format(task_id),file=sys.stderr); sys.exit(1)

def cmd_edit(args, data):
    if not args: print("Usage: edit ID --title NEW TITLE",file=sys.stderr); sys.exit(1)
    try: task_id=int(args[0])
    except ValueError: print("Invalid task id: {}".format(args[0]),file=sys.stderr); sys.exit(1)
    new_title=None; i=1
    while i<len(args):
        if args[i]=="--title":
            if i+1>=len(args): print("--title requires a value",file=sys.stderr); sys.exit(1)
            new_title=args[i+1]; i+=2
            while i<len(args) and not args[i].startswith("--"): new_title+=" "+args[i]; i+=1
        else: i+=1
    if new_title is None: print("--title is required",file=sys.stderr); sys.exit(1)
    for t in data["tasks"]:
        if t["id"]==task_id:
            old_title=t["title"]; t["title"]=new_title
            data["undo_stack"].append({"type":"edit","task_id":task_id,"old_title":old_title})
            save_tasks(data); print("Edited {}".format(task_id)); return
    print("No such task: {}".format(task_id),file=sys.stderr); sys.exit(1)

def cmd_search(args, data):
    if not args: print("Usage: search TEXT",file=sys.stderr); sys.exit(1)
    query=" ".join(args).lower(); matches=[]
    for t in sorted(data["tasks"],key=lambda x:x["id"]):
        if query in t["title"].lower(): matches.append(t)
    if not matches: print("No matches")
    else:
        for t in matches: print(task_line(t))

def cmd_export(args, data):
    fmt=None; i=0
    while i<len(args):
        if args[i]=="--format":
            if i+1>=len(args): print("--format requires a value",file=sys.stderr); sys.exit(1)
            fmt=args[i+1]; i+=2
        else: i+=1
    if fmt is None: print("--format json|csv is required",file=sys.stderr); sys.exit(1)
    tasks=sorted(data["tasks"],key=lambda t:t["id"])
    if fmt=="json":
        ed=[]
        for t in tasks: ed.append({"id":t["id"],"title":t["title"],"done":t["done"],"priority":t.get("priority","medium"),"tags":t.get("tags",[]),"due":t.get("due")})
        print(json.dumps(ed,indent=2))
    elif fmt=="csv":
        print("id,title,done,priority,tags,due")
        for t in tasks:
            ts=";".join(t.get("tags",[])); ds=t.get("due",""); dr="true" if t["done"] else "false"
            print("{},{},{},{},{},{}".format(t["id"],t["title"],dr,t.get("priority","medium"),ts,ds))
    else: print("Unknown format: {}".format(fmt),file=sys.stderr); sys.exit(1)

def cmd_stats(args, data):
    oc=sum(1 for t in data["tasks"] if not t["done"])
    dc=sum(1 for t in data["tasks"] if t["done"])
    print("open: {}".format(oc)); print("done: {}".format(dc)); print("total: {}".format(len(data["tasks"])))

def cmd_undo(args, data):
    if not data["undo_stack"]: print("Nothing to undo",file=sys.stderr); sys.exit(1)
    entry=data["undo_stack"].pop()
    if entry["type"]=="add":
        task=entry["task"]
        data["tasks"]=[t for t in data["tasks"] if t["id"]!=task["id"]]
        data["next_id"]=entry["prev_next_id"]
    elif entry["type"]=="done":
        tid=entry["task_id"]
        for t in data["tasks"]:
            if t["id"]==tid: t["done"]=entry["prev_done"]; break
    elif entry["type"]=="delete":
        dt=entry["task"]; idx=entry["index"]
        data["tasks"].insert(idx,dt); data["next_id"]=entry["prev_next_id"]
    elif entry["type"]=="edit":
        tid=entry["task_id"]; ot=entry["old_title"]
        for t in data["tasks"]:
            if t["id"]==tid: t["title"]=ot; break
    save_tasks(data); print("Undone")

COMMANDS={"add":cmd_add,"list":cmd_list,"done":cmd_done,"delete":cmd_delete,"edit":cmd_edit,"search":cmd_search,"export":cmd_export,"stats":cmd_stats,"undo":cmd_undo}

def main():
    if len(sys.argv)<2: print("Usage: tasks.py <command> [args]",file=sys.stderr); sys.exit(1)
    command=sys.argv[1]; args=sys.argv[2:]
    if command not in COMMANDS: print("Unknown command: {}".format(command),file=sys.stderr); sys.exit(1)
    data=load_tasks(); COMMANDS[command](args,data)

if __name__=="__main__": main()
