#!/usr/bin/env python3
"""Command-line task manager."""

import json
import sys
import os
from datetime import datetime, date


DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def make_task_line(task):
    done_marker = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']} {done_marker} {task['title']}"
    if task.get("priority") == "high":
        line += " (high)"
    elif task.get("priority") == "low":
        line += " (low)"
    if task.get("tags"):
        tags_str = " ".join(f"#{t}" for t in task["tags"])
        line += " " + tags_str
    if task.get("due"):
        line += f" due:{task['due']}"
    return line


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)
