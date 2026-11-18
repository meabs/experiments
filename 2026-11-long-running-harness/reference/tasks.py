#!/usr/bin/env python3
"""Reference solution used to validate the hidden tests. Never shown to agents."""
import argparse, csv, datetime, io, json, os, sys

DB = 'tasks.json'


def load():
    if os.path.exists(DB):
        with open(DB) as f:
            return json.load(f)
    return {'next_id': 1, 'tasks': [], 'history': []}


def save(db):
    with open(DB, 'w') as f:
        json.dump(db, f)


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def snapshot(db):
    return {'next_id': db['next_id'], 'tasks': json.loads(json.dumps(db['tasks']))}


def mutate(db):
    db['history'].append(snapshot(db))


def line(t):
    s = '%d [%s] %s' % (t['id'], 'x' if t['done'] else ' ', t['title'])
    if t['priority'] != 'medium':
        s += ' (%s)' % t['priority']
    if t['tags']:
        s += ' ' + ' '.join('#' + g for g in t['tags'])
    if t['due']:
        s += ' due:' + t['due']
    return s


def find(db, i):
    for t in db['tasks']:
        if t['id'] == i:
            return t
    fail('No such task: %s' % i)


def valid_date(s):
    try:
        datetime.date.fromisoformat(s)
        if len(s) != 10:
            raise ValueError
    except ValueError:
        fail('Invalid date: %s' % s)
    return s


def main(argv):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add')
    a.add_argument('title')
    a.add_argument('--priority', default='medium')
    a.add_argument('--tag', action='append', default=[])
    a.add_argument('--due')
    l = sub.add_parser('list')
    l.add_argument('--sort')
    l.add_argument('--tag')
    l.add_argument('--overdue', action='store_true')
    l.add_argument('--today')
    for c in ('done', 'delete'):
        x = sub.add_parser(c)
        x.add_argument('id', type=int)
    e = sub.add_parser('edit')
    e.add_argument('id', type=int)
    e.add_argument('--title', nargs='+', required=True)
    s = sub.add_parser('search')
    s.add_argument('text')
    ex = sub.add_parser('export')
    ex.add_argument('--format', required=True, choices=['json', 'csv'])
    sub.add_parser('stats')
    sub.add_parser('undo')
    try:
        args = p.parse_args(argv)
    except SystemExit as err:
        sys.exit(1 if err.code else 0)
    db = load()
    c = args.cmd
    if c == 'add':
        if args.priority not in ('high', 'medium', 'low'):
            fail('Invalid priority: %s' % args.priority)
        if args.due:
            valid_date(args.due)
        mutate(db)
        t = {'id': db['next_id'], 'title': args.title, 'done': False, 'priority': args.priority,
             'tags': args.tag, 'due': args.due}
        db['next_id'] += 1
        db['tasks'].append(t)
        save(db)
        print('Added %d' % t['id'])
    elif c == 'list':
        ts = list(db['tasks'])
        if args.tag:
            ts = [t for t in ts if args.tag in t['tags']]
        if args.overdue:
            today = args.today or datetime.date.today().isoformat()
            ts = [t for t in ts if not t['done'] and t['due'] and t['due'] < today]
        if args.sort == 'priority':
            rank = {'high': 0, 'medium': 1, 'low': 2}
            ts.sort(key=lambda t: (rank[t['priority']], t['id']))
        if not ts:
            print('No tasks')
        for t in ts:
            print(line(t))
    elif c in ('done', 'delete', 'edit'):
        t = find(db, args.id)
        mutate(db)
        if c == 'done':
            t['done'] = True
            print('Done %d' % t['id'])
        elif c == 'delete':
            db['tasks'].remove(t)
            print('Deleted %d' % t['id'])
        else:
            t['title'] = ' '.join(args.title)
            print('Edited %d' % t['id'])
        save(db)
    elif c == 'search':
        ts = [t for t in db['tasks'] if args.text.lower() in t['title'].lower()]
        if not ts:
            print('No matches')
        for t in ts:
            print(line(t))
    elif c == 'export':
        if args.format == 'json':
            print(json.dumps([{k: t[k] for k in ('id', 'title', 'done', 'priority', 'tags', 'due')}
                              for t in db['tasks']]))
        else:
            print('id,title,done,priority,tags,due')
            for t in db['tasks']:
                print('%d,%s,%s,%s,%s,%s' % (t['id'], t['title'], 'true' if t['done'] else 'false',
                                             t['priority'], ';'.join(t['tags']), t['due'] or ''))
    elif c == 'stats':
        n = len(db['tasks'])
        d = sum(1 for t in db['tasks'] if t['done'])
        print('open: %d\ndone: %d\ntotal: %d' % (n - d, d, n))
    elif c == 'undo':
        if not db['history']:
            fail('Nothing to undo')
        prev = db['history'].pop()
        db['next_id'], db['tasks'] = prev['next_id'], prev['tasks']
        save(db)
        print('Undone')


if __name__ == '__main__':
    main(sys.argv[1:])
