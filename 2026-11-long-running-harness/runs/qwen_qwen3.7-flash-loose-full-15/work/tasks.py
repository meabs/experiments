#!/usr/bin/env python3
import json, os, sys, copy
from datetime import datetime, date

DATA_FILE = 'tasks.json'
HISTORY_FILE = 'history.json'


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return {}, 1
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        raw_tasks = data.get('tasks', {})
        tasks = {int(k): v for k, v in raw_tasks.items()}
        return tasks, data.get('next_id', 1)
    except (json.JSONDecodeError, KeyError, ValueError):
        return {}, 1


def save_tasks(tasks, next_id):
    with open(DATA_FILE, 'w') as f:
        json.dump({'tasks': tasks, 'next_id': next_id}, f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)


def record_undo(tasks, next_id):
    history = load_history()
    history.append({'tasks': copy.deepcopy(tasks), 'next_id': next_id})
    save_history(history)


def do_undo():
    history = load_history()
    if not history:
        print('Nothing to undo', file=sys.stderr)
        sys.exit(1)
    prev = history.pop()
    save_tasks(prev['tasks'], prev['next_id'])
    save_history(history)
    print('Undone')


def validate_priority(v):
    return v in ('high', 'medium', 'low')


def validate_date(v):
    try:
        datetime.strptime(v, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def format_task_line(task):
    tid = task['id']
    status = 'x' if task['done'] else ' '
    title = task['title']
    suffixes = []
    priority = task.get('priority', 'medium')
    if priority == 'high':
        suffixes.append('(high)')
    elif priority == 'low':
        suffixes.append('(low)')
    tags = task.get('tags', [])
    if tags:
        suffixes.append(' '.join('#' + t for t in tags))
    due = task.get('due')
    if due:
        suffixes.append('due:' + due)
    if suffixes:
        return '{} [{}] {} {}'.format(tid, status, title, ' '.join(suffixes))
    else:
        return '{} [{}] {}'.format(tid, status, title)


def cmd_add(args):
    if not args:
        print('Usage: add TITLE', file=sys.stderr)
        sys.exit(1)
    title_parts = []
    priority = 'medium'
    tags = []
    due = None
    i = 0
    while i < len(args):
        if args[i] == '--priority':
            if i + 1 >= len(args):
                print('Missing value for --priority', file=sys.stderr)
                sys.exit(1)
            priority = args[i + 1]
            if not validate_priority(priority):
                print('Invalid priority: ' + priority, file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == '--tag':
            if i + 1 >= len(args):
                print('Missing value for --tag', file=sys.stderr)
                sys.exit(1)
            tags.append(args[i + 1])
            i += 2
        elif args[i] == '--due':
            if i + 1 >= len(args):
                print('Missing value for --due', file=sys.stderr)
                sys.exit(1)
            due = args[i + 1]
            if not validate_date(due):
                print('Invalid date: ' + due, file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            title_parts.append(args[i])
            i += 1
    title = ' '.join(title_parts)
    tasks, next_id = load_tasks()
    task = {'id': next_id, 'title': title, 'done': False, 'priority': priority, 'tags': tags, 'due': due}
    tasks[next_id] = task
    new_next_id = next_id + 1
    save_tasks(tasks, new_next_id)
    record_undo(tasks, new_next_id)
    print('Added ' + str(next_id))


def cmd_list(args):
    tasks, _ = load_tasks()
    sort_by = None
    tag_filter = None
    overdue = False
    today_arg = None
    i = 0
    while i < len(args):
        if args[i] == '--sort' and i + 1 < len(args):
            sort_by = args[i + 1]
            i += 2
        elif args[i] == '--tag' and i + 1 < len(args):
            tag_filter = args[i + 1]
            i += 2
        elif args[i] == '--overdue':
            overdue = True
            i += 1
        elif args[i] == '--today' and i + 1 < len(args):
            today_arg = args[i + 1]
            i += 2
        else:
            i += 1
    all_tasks = list(tasks.values())
    if tag_filter:
        all_tasks = [t for t in all_tasks if tag_filter in t.get('tags', [])]
    if overdue:
        today = date.today()
        if today_arg:
            try:
                today = datetime.strptime(today_arg, '%Y-%m-%d').date()
            except ValueError:
                print('Invalid date: ' + today_arg, file=sys.stderr)
                sys.exit(1)
        all_tasks = [t for t in all_tasks if not t['done'] and t.get('due') and t['due'] < today.strftime('%Y-%m-%d')]
    if sort_by == 'priority':
        po = {'high': 0, 'medium': 1, 'low': 2}
        all_tasks.sort(key=lambda t: (po.get(t.get('priority', 'medium'), 1), t['id']))
    else:
        all_tasks.sort(key=lambda t: t['id'])
    if not all_tasks:
        print('No tasks')
    else:
        for task in all_tasks:
            print(format_task_line(task))


def cmd_done(args):
    if not args:
        print('Usage: done ID', file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print('No such task: ' + args[0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print('No such task: ' + str(task_id), file=sys.stderr)
        sys.exit(1)
    tasks[task_id]['done'] = True
    save_tasks(tasks, next_id)
    record_undo(tasks, next_id)
    print('Done ' + str(task_id))


def cmd_delete(args):
    if not args:
        print('Usage: delete ID', file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print('No such task: ' + args[0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print('No such task: ' + str(task_id), file=sys.stderr)
        sys.exit(1)
    del tasks[task_id]
    save_tasks(tasks, next_id)
    record_undo(tasks, next_id)
    print('Deleted ' + str(task_id))


def cmd_edit(args):
    if not args:
        print('Usage: edit ID --title NEW TITLE', file=sys.stderr)
        sys.exit(1)
    try:
        task_id = int(args[0])
    except ValueError:
        print('No such task: ' + args[0], file=sys.stderr)
        sys.exit(1)
    tasks, next_id = load_tasks()
    if task_id not in tasks:
        print('No such task: ' + str(task_id), file=sys.stderr)
        sys.exit(1)
    # Find --title flag and extract new title
    title_idx = None
    for i, arg in enumerate(args):
        if arg == '--title':
            title_idx = i
            break
    if title_idx is None or title_idx + 1 >= len(args):
        print('Usage: edit ID --title NEW TITLE', file=sys.stderr)
        sys.exit(1)
    new_title = ' '.join(args[title_idx + 1:])
    tasks[task_id]['title'] = new_title
    save_tasks(tasks, next_id)
    record_undo(tasks, next_id)
    print('Edited ' + str(task_id))


def cmd_search(args):
    if not args:
        print('Usage: search TEXT', file=sys.stderr)
        sys.exit(1)
    query = ' '.join(args).lower()
    tasks, _ = load_tasks()
    matches = [t for t in tasks.values() if query in t['title'].lower()]
    matches.sort(key=lambda t: t['id'])
    if not matches:
        print('No matches')
    else:
        for task in matches:
            print(format_task_line(task))


def cmd_export(args):
    fmt = None
    i = 0
    while i < len(args):
        if args[i] == '--format' and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not fmt or fmt not in ('json', 'csv'):
        print('Usage: export --format json|csv', file=sys.stderr)
        sys.exit(1)
    tasks, _ = load_tasks()
    all_tasks = sorted(tasks.values(), key=lambda t: t['id'])
    if fmt == 'json':
        result = []
        for task in all_tasks:
            result.append({
                'id': task['id'],
                'title': task['title'],
                'done': task['done'],
                'priority': task.get('priority', 'medium'),
                'tags': task.get('tags', []),
                'due': task.get('due', None)
            })
        print(json.dumps(result))
    elif fmt == 'csv':
        print('id,title,done,priority,tags,due')
        for task in all_tasks:
            done_str = 'true' if task['done'] else 'false'
            tags_str = ';'.join(task.get('tags', []))
            due_str = task.get('due', '') or ''
            row = '{},{},{},{},{},{}'.format(
                task['id'], task['title'], done_str,
                task.get('priority', 'medium'), tags_str, due_str)
            print(row)


def cmd_stats(args):
    tasks, _ = load_tasks()
    open_count = sum(1 for t in tasks.values() if not t['done'])
    done_count = sum(1 for t in tasks.values() if t['done'])
    total = len(tasks)
    print('open: ' + str(open_count))
    print('done: ' + str(done_count))
    print('total: ' + str(total))


COMMANDS = {
    'add': cmd_add,
    'list': cmd_list,
    'done': cmd_done,
    'delete': cmd_delete,
    'edit': cmd_edit,
    'search': cmd_search,
    'export': cmd_export,
    'stats': cmd_stats,
}


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 tasks.py <command> [args]', file=sys.stderr)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command == 'undo':
        do_undo()
    elif command in COMMANDS:
        COMMANDS[command](args)
    else:
        print('Unknown command: ' + command, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
