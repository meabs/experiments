#!/usr/bin/env python3
"""Command-line task manager."""
import json, os, sys
from datetime import date, datetime

DATA_FILE = "tasks.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

def fmt(t):
    s = "[x]" if t["done"] else "[ ]"
    line = f'{t["id"]} {s} {t["title"]}'
    p = t.get("priority", "medium")
    if p == "high": line += " (high)"
    elif p == "low": line += " (low)"
    for tg in t.get("tags", []): line += f" #{tg}"
    d = t.get("due")
    if d: line += f" due:{d}"
    return line

def err(m): print(m, file=sys.stderr); sys.exit(1)

def _flags(args):
    pri="medium"; tags=[]; due=None; skip=set(); i=0
    while i < len(args):
        a = args[i]
        if a == "--priority":
            if i+1>=len(args): err("--priority needs value")
            skip.add(i); i+=1; v=args[i]; skip.add(i)
            if v not in ("high","medium","low"): err(f"Invalid priority: {v}")
            pri=v
        elif a == "--tag":
            if i+1>=len(args): err("--tag needs value")
            skip.add(i); i+=1; v=args[i]; skip.add(i); tags.append(v)
        elif a == "--due":
            if i+1>=len(args): err("--due needs value")
            skip.add(i); i+=1; v=args[i]; skip.add(i)
            try: datetime.strptime(v,"%Y-%m-%d")
            except ValueError: err(f"Invalid date: {v}")
            due=v
        elif a.startswith("--"): err(f"Unknown option: {a}")
        i+=1
    return skip,pri,tags,due

def _undo(data):
    data["history"].append(json.dumps({"tasks":data["tasks"],"next_id":data["next_id"]}))

def cmd_add(args):
    d=load_data()
    if not args: err("Missing title")
    skip,pri,tags,due=_flags(args)
    title=" ".join(a for i,a in enumerate(args) if i not in skip)
    if not title: err("Missing title")
    _undo(d)
    t={"id":d["next_id"],"title":title,"done":False,"priority":pri,"tags":tags,"due":due}
    d["tasks"].append(t); d["next_id"]+=1; save_data(d)
    print(f"Added {t['id']}")

def cmd_list(args):
    d=load_data(); sb=None; tf=None; ov=False; ts=None; i=0
    while i<len(args):
        a=args[i]
        if a=="--sort":
            if i+1>=len(args): err("--sort needs value")
            i+=1; sb=args[i]
        elif a=="--tag":
            if i+1>=len(args): err("--tag filter needs value")
            i+=1; tf=args[i]
        elif a=="--overdue": ov=True
        elif a=="--today":
            if i+1>=len(args): err("--today needs value")
            i+=1; ts=args[i]
        else: err(f"Unknown option: {a}")
        i+=1
    tasks=list(d["tasks"])
    if tf: tasks=[t for t in tasks if tf in t.get("tags",[])]
    if ov:
        if ts is None: ts=date.today().isoformat()
        tasks=[t for t in tasks if not t["done"] and t.get("due") and t["due"]<ts]
    if sb=="priority":
        po={"high":0,"medium":1,"low":2}
        tasks.sort(key=lambda t:(po.get(t.get("priority","medium"),1),t["id"]))
    else: tasks.sort(key=lambda t:t["id"])
    if not tasks: print("No tasks"); return
    for t in tasks: print(fmt(t))

def cmd_done(args):
    d=load_data()
    if not args: err("Missing ID")
    try: tid=int(args[0])
    except ValueError: err(f"Invalid ID: {args[0]}")
    t=next((t for t in d["tasks"] if t["id"]==tid),None)
    if t is None: err(f"No such task: {tid}")
    _undo(d); t["done"]=True; save_data(d)
    print(f"Done {tid}")

def cmd_delete(args):
    d=load_data()
    if not args: err("Missing ID")
    try: tid=int(args[0])
    except ValueError: err(f"Invalid ID: {args[0]}")
    t=next((t for t in d["tasks"] if t["id"]==tid),None)
    if t is None: err(f"No such task: {tid}")
    _undo(d); d["tasks"]=[t for t in d["tasks"] if t["id"]!=tid]; save_data(d)
    print(f"Deleted {tid}")

def cmd_edit(args):
    d=load_data()
    if not args: err("Missing ID")
    try: tid=int(args[0])
    except ValueError: err(f"Invalid ID: {args[0]}")
    t=next((t for t in d["tasks"] if t["id"]==tid),None)
    if t is None: err(f"No such task: {tid}")
    nt=None; i=1
    while i<len(args):
        if args[i]=="--title":
            if i+1>=len(args): err("--title needs value")
            nt=" ".join(args[i+1:]); break
        i+=1
    if nt is None: err("Missing --title")
    _undo(d); t["title"]=nt; save_data(d)
    print(f"Edited {tid}")

def cmd_search(args):
    d=load_data()
    if not args: err("Missing search text")
    q=" ".join(args).lower()
    m=sorted([t for t in d["tasks"] if q in t["title"].lower()],key=lambda t:t["id"])
    if not m: print("No matches"); return
    for t in m: print(fmt(t))

def cmd_export(args):
    d=load_data(); ft=None; i=0
    while i<len(args):
        if args[i]=="--format":
            if i+1>=len(args): err("--format needs value")
            i+=1; ft=args[i]
            if ft not in ("json","csv"): err(f"Invalid format: {ft}")
        i+=1
    if ft is None: err("Missing --format")
    tasks=sorted(d["tasks"],key=lambda t:t["id"])
    if ft=="json":
        out=[{"id":t["id"],"title":t["title"],"done":t["done"],
              "priority":t.get("priority","medium"),"tags":t.get("tags",[]),
              "due":t.get("due")} for t in tasks]
        print(json.dumps(out,indent=2))
    else:
        print("id,title,done,priority,tags,due")
        for t in tasks:
            ds="true" if t["done"] else "false"
            tg=t.get("tags",[]) or []; ts=";".join(tg)
            du=t.get("due") or ""
            print(f'{t["id"]},{t["title"]},{ds},{t.get("priority","medium")},{ts},{du}')

def cmd_stats(args):
    d=load_data()
    oc=sum(1 for t in d["tasks"] if not t["done"])
    dc=sum(1 for t in d["tasks"] if t["done"])
    print(f"open: {oc}\ndone: {dc}\ntotal: {len(d['tasks'])}")

def cmd_undo(args):
    d=load_data()
    if not d["history"]: err("Nothing to undo")
    prev=json.loads(d["history"].pop())
    d["tasks"]=prev["tasks"]; d["next_id"]=prev["next_id"]; save_data(d)
    print("Undone")

CMD={
    "add":cmd_add,"list":cmd_list,"done":cmd_done,"delete":cmd_delete,
    "edit":cmd_edit,"search":cmd_search,"export":cmd_export,
    "stats":cmd_stats,"undo":cmd_undo,
}

def main():
    if len(sys.argv)<2: err("Usage: python3 tasks.py <command> [args]")
    c=sys.argv[1]
    if c not in CMD: err(f"Unknown command: {c}")
    CMD[c](sys.argv[2:])

if __name__=="__main__": main()
