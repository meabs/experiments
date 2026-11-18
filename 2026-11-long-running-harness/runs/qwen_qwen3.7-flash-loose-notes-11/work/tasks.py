#!/usr/bin/env python3
"""Command-line task manager."""

import copy
import json
import os
import sys
from datetime import date, datetime

DATA_FILE = "tasks.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "next_id": 1, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def snapshot(data):
    return {
        "tasks": copy.deepcopy(data["tasks"]),
        "next_id": data["next_id"],
    }


def make_task_line(task):
    prefix = "[x]" if task["done"] else "[ ]"
    parts = [f"{task['id']} {prefix} {task['title']}"]
    if task.get("priority") == "high":
        parts.append("(high)")
    elif task.get("priority") == "low":
        parts.append("(low)")
    for tag in task.get("tags", []):
        parts.append(f"#{tag}")
    if task.get("due"):
        parts.append(f"due:{task['due']}")
    return " ".join(parts)


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
