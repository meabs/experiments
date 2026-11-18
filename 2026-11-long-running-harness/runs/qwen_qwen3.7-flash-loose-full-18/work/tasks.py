#!/usr/bin/env python3
import sys, json, os, copy
from datetime import datetime, date

DATA_FILE = 'tasks.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'tasks': [], 'undo_history': [], 'next_id': 1}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def next_id(tasks, data_next_id):
    return data_next_id

def task_line(task):
    dm = '[x]' if task['done'] else '[ ]'
    p = [str(task['id']), dm, task['title']]
    if task.get('priority') == 'high':
        p.append('(high)')
    elif task.get('priority') == 'low':
        p.append('(low)')
    for tg in task.get('tags', []):
        p.append('#' + tg)
    if task.get('due'):
        p.append('due:' + task['due'])
    return ' '.join(p)

def cmd_add(args, data):
    title_parts = []
    priority = None
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == '--priority':
            if i + 1 >= len(args):
                print('--priority requires a value', file=sys.stderr); sys.exit(1)
            priority = args[i + 1]
            if priority not in ('high', 'medium', 'low'):
                print(f'Invalid priority: {priority}', file=sys.stderr); sys.exit(1)
            i += 2
        elif args[i] == '--tag':
            if i + 1 >= len(args):
                print('--tag requires a value', file=sys.stderr); sys.exit(1)
            tags.append(args[i + 1]); i += 2
        elif args[i] == '--due':
            if i + 1 >= len(args):
                print('--due requires a value', file=sys.stderr); sys.exit(1)
            due = args[i + 1]
            try:
                datetime.strptime(due, '%Y-%m-%d')
            except ValueError:
                print(f'Invalid date: {due}', file=sys.stderr); sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i]); i += 1
    if not title_parts:
        print('Usage: add TITLE [--priority high|medium|low] [--tag TAG]... [--due YYYY-MM-DD]', file=sys.stderr); sys.exit(1)
    title = ' '.join(title_parts)
    nid = next_id(data['tasks'], data['next_id'])
    data['undo_history'].append({'type': 'add', 'prev_tasks': copy.deepcopy(data['tasks']), 'next_id': nid})
    data['next_id'] = nid + 1
    new_task = {'id': nid, 'title': title, 'done': False, 'priority': priority or 'medium', 'tags': tags, 'due': due}
    data['tasks'].append(new_task)
    save_data(data)
    print(f'Added {nid}')

def cmd_list(args, data):
    show_tag = None
    sort_priority = False
    overdue = False
    today_str = None
    i = 0
    while i < len(args):
        if args[i] == '--tag':
            if i + 1 >= len(args):
                print('--tag requires a value', file=sys.stderr); sys.exit(1)
            show_tag = args[i + 1]; i += 2
        elif args[i] == '--sort':
            if i + 1 >= len(args):
                print('--sort requires a value', file=sys.stderr); sys.exit(1)
            sort_priority = args[i + 1] == 'priority'; i += 2
        elif args[i] == '--overdue':
            overdue = True; i += 1
        elif args[i] == '--today':
            if i + 1 >= len(args):
                print('--today requires a date', file=sys.stderr); sys.exit(1)
            today_str = args[i + 1]
            try:
                datetime.strptime(today_str, '%Y-%m-%d')
            except ValueError:
                print(f'Invalid date: {today_str}', file=sys.stderr); sys.exit(1)
            i += 2
        else:
            i += 1
    tasks = list(data['tasks'])
    if overdue:
        today = today_str if today_str else date.today().isoformat()
        tasks = [t for t in tasks if not t['done'] and t.get('due') and t['due'] < today]
    if show_tag:
        tasks = [t for t in tasks if show_tag in t.get('tags', [])]
    if not tasks:
        print('No tasks'); return
    if sort_priority:
        po = {'high': 0, 'medium': 1, 'low': 2}
        tasks = sorted(tasks, key=lambda t: (po.get(t.get('priority', 'medium'), 1), t['id']))
    for t in tasks:
        print(task_line(t))

def cmd_done(args, data):
    if not args:
        print('Usage: done ID', file=sys.stderr); sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f'No such task: {args[0]}', file=sys.stderr); sys.exit(1)
    task = None
    for t in data['tasks']:
        if t['id'] == task_id:
            task = t; break
    if task is None:
        print(f'No such task: {task_id}', file=sys.stderr); sys.exit(1)
    data['undo_history'].append({'type': 'done', 'task_id': task_id, 'prev_done': task['done'], 'prev_tasks': copy.deepcopy(data['tasks'])})
    task['done'] = True
    save_data(data)
    print(f'Done {task_id}')


def cmd_delete(args, data):
    if not args:
        print('Usage: delete ID', file=sys.stderr); sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f'No such task: {args[0]}', file=sys.stderr); sys.exit(1)
    task = None
    for t in data['tasks']:
        if t['id'] == task_id:
            task = t; break
    if task is None:
        print(f'No such task: {task_id}', file=sys.stderr); sys.exit(1)
    data['undo_history'].append({'type': 'delete', 'deleted_task': task, 'prev_tasks': copy.deepcopy(data['tasks']), 'next_id': data['next_id']})
    data['tasks'] = [t for t in data['tasks'] if t['id'] != task_id]
    save_data(data)
    print(f'Deleted {task_id}')

def cmd_edit(args, data):
    if not args:
        print('Usage: edit ID --title NEW TITLE', file=sys.stderr); sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print(f'No such task: {args[0]}', file=sys.stderr); sys.exit(1)
    task = None
    for t in data['tasks']:
        if t['id'] == task_id:
            task = t; break
    if task is None:
        print(f'No such task: {task_id}', file=sys.stderr); sys.exit(1)
    new_title = None
    i = 1
    while i < len(args):
        if args[i] == '--title':
            if i + 1 >= len(args):
                print('--title is required', file=sys.stderr); sys.exit(1)
            new_title = args[i + 1]; i += 2
        else:
            i += 1
    if new_title is None:
        print('--title is required', file=sys.stderr); sys.exit(1)
    data['undo_history'].append({'type': 'edit', 'task_id': task_id, 'prev_title': task['title'], 'prev_tasks': copy.deepcopy(data['tasks'])})
    task['title'] = new_title
    save_data(data)
    print(f'Edited {task_id}')


def cmd_search(args, data):
    if not args:
        print('Usage: search TEXT', file=sys.stderr); sys.exit(1)
    query = ' '.join(args).lower()
    matches = [t for t in data['tasks'] if query in t['title'].lower()]
    if not matches:
        print('No matches'); return
    matches.sort(key=lambda t: t['id'])
    for t in matches:
        print(task_line(t))

def cmd_export(args, data):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == '--format':
            if i + 1 >= len(args):
                print('--format requires json or csv', file=sys.stderr); sys.exit(1)
            fmt = args[i + 1]
            if fmt not in ('json', 'csv'):
                print(f'Invalid format: {fmt}', file=sys.stderr); sys.exit(1)
            i += 2
        else:
            i += 1
    if fmt is None:
        print('Usage: export --format json|csv', file=sys.stderr); sys.exit(1)
    tasks = sorted(data['tasks'], key=lambda t: t['id'])
    if fmt == 'json':
        result = []
        for t in tasks:
            result.append({'id': t['id'], 'title': t['title'], 'done': t['done'], 'priority': t.get('priority', 'medium'), 'tags': t.get('tags', []), 'due': t.get('due')})
        print(json.dumps(result))
    elif fmt == 'csv':
        print('id,title,done,priority,tags,due')
        for t in tasks:
            tags_str = ';'.join(t.get('tags', []))
            due_str = t.get('due') or ''
            done_s = 'true' if t['done'] else 'false'
            pri = t.get('priority', 'medium')
            print(str(t['id']) + ',' + t['title'] + ',' + done_s + ',' + pri + ',' + tags_str + ',' + due_str)


def cmd_stats(args, data):
    tasks = data['tasks']
    open_count = sum(1 for t in tasks if not t['done'])
    done_count = sum(1 for t in tasks if t['done'])
    total = len(tasks)
    print(f'open: {open_count}')
    print(f'done: {done_count}')
    print(f'total: {total}')


def cmd_undo(args, data):
    if not data['undo_history']:
        print('Nothing to undo', file=sys.stderr); sys.exit(1)
    entry = data['undo_history'].pop()
    data['tasks'] = entry['prev_tasks']
    if 'next_id' in entry:
        data['next_id'] = entry['next_id']
    save_data(data)
    print('Undone')


COMMANDS = {'add': cmd_add, 'list': cmd_list, 'done': cmd_done, 'delete': cmd_delete, 'edit': cmd_edit, 'search': cmd_search, 'export': cmd_export, 'stats': cmd_stats, 'undo': cmd_undo}


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 tasks.py <command> [args]', file=sys.stderr); sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command not in COMMANDS:
        print(f'Unknown command: {command}', file=sys.stderr); sys.exit(1)
    data = load_data()
    COMMANDS[command](args, data)


if __name__ == '__main__':
    main()
