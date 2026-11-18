#!/usr/bin/env python3
"""Command-line task manager."""

import csv
import io
import json
import os
import sys
from datetime import date, datetime


DATA_FILE = "tasks.json"
HISTORY_FILE = "tasks_history.json"


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return [], 1
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        tasks = data.get("tasks", [])
        next_id = data.get("next_id", 1)
        return tasks, next_id
    except (json.JSONDecodeError, KeyError):
        return [], 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, "w") as f:
        json.dump({"tasks": tasks, "next_id": next_id}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def push_history(state):
    history = load_history()
    history.append(state)
    if len(history) > 100:
        history = history[-100:]
    save_history(history)


def pop_history():
    history = load_history()
    if not history:
        print("Nothing to undo", file=sys.stderr)
        sys.exit(1)
    state = history.pop()
    save_history(history)
    return state


def task_line(task):
    status = "[x]" if task["done"] else "[ ]"
    line = "{} {} {}".format(task["id"], status, task["title"])
    priority = task.get("priority", "medium")
    if priority == "high":
        line += " (high)"
    elif priority == "low":
        line += " (low)"
    tags = task.get("tags", [])
    for tag in tags:
        line += " #{}".format(tag)
    due = task.get("due")
    if due:
        line += " due:{}".format(due)
    return line


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
