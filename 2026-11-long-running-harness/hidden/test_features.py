"""Hidden acceptance tests: one TestCase class per feature (F01..F12).

The target is set with TASKS_PY (path to the candidate tasks.py). Each test runs the CLI in a
fresh temp directory, so tests never share state. Agents never see this file.
"""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

TASKS = os.environ.get('TASKS_PY', 'tasks.py')


class Base(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.cwd = self._d.name

    def tearDown(self):
        self._d.cleanup()

    def run_cli(self, *args):
        p = subprocess.run([sys.executable, TASKS, *args], cwd=self.cwd, capture_output=True,
                           text=True, timeout=20)
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    def ok(self, *args):
        code, out, err = self.run_cli(*args)
        self.assertEqual(code, 0, 'args=%r stderr=%r' % (args, err))
        return out

    def bad(self, *args):
        code, out, err = self.run_cli(*args)
        self.assertEqual(code, 1, 'args=%r should exit 1' % (args,))
        return err


class F01Add(Base):
    def test_add_prints_id(self):
        self.assertEqual(self.ok('add', 'Buy milk'), 'Added 1')
        self.assertEqual(self.ok('add', 'Walk dog'), 'Added 2')

    def test_state_persists(self):
        self.ok('add', 'one')
        self.assertTrue(os.path.exists(os.path.join(self.cwd, 'tasks.json')))


class F02List(Base):
    def test_empty(self):
        self.assertEqual(self.ok('list'), 'No tasks')

    def test_lines(self):
        self.ok('add', 'Buy milk')
        self.ok('add', 'Walk dog')
        self.assertEqual(self.ok('list'), '1 [ ] Buy milk\n2 [ ] Walk dog')


class F03Done(Base):
    def test_done(self):
        self.ok('add', 'a')
        self.ok('add', 'b')
        self.assertEqual(self.ok('done', '2'), 'Done 2')
        self.assertEqual(self.ok('list'), '1 [ ] a\n2 [x] b')

    def test_unknown(self):
        self.assertEqual(self.bad('done', '9'), 'No such task: 9')


class F04Delete(Base):
    def test_delete_and_ids_not_reused(self):
        self.ok('add', 'a')
        self.ok('add', 'b')
        self.assertEqual(self.ok('delete', '2'), 'Deleted 2')
        self.assertEqual(self.ok('list'), '1 [ ] a')
        self.assertEqual(self.ok('add', 'c'), 'Added 3')

    def test_unknown(self):
        self.assertEqual(self.bad('delete', '4'), 'No such task: 4')


class F05Priority(Base):
    def test_suffix(self):
        self.ok('add', 'a', '--priority', 'high')
        self.ok('add', 'b')
        self.ok('add', 'c', '--priority', 'low')
        self.assertEqual(self.ok('list'), '1 [ ] a (high)\n2 [ ] b\n3 [ ] c (low)')

    def test_sort(self):
        self.ok('add', 'a', '--priority', 'low')
        self.ok('add', 'b', '--priority', 'high')
        self.ok('add', 'c')
        self.ok('add', 'd', '--priority', 'high')
        self.assertEqual(self.ok('list', '--sort', 'priority'),
                         '2 [ ] b (high)\n4 [ ] d (high)\n3 [ ] c\n1 [ ] a (low)')

    def test_invalid(self):
        self.assertEqual(self.bad('add', 'a', '--priority', 'urgent'), 'Invalid priority: urgent')


class F06Tags(Base):
    def test_suffix_and_filter(self):
        self.ok('add', 'a', '--tag', 'work', '--tag', 'home')
        self.ok('add', 'b', '--tag', 'home')
        self.ok('add', 'c')
        self.assertEqual(self.ok('list'), '1 [ ] a #work #home\n2 [ ] b #home\n3 [ ] c')
        self.assertEqual(self.ok('list', '--tag', 'work'), '1 [ ] a #work #home')

    def test_after_priority(self):
        self.ok('add', 'a', '--priority', 'high', '--tag', 'x')
        self.assertEqual(self.ok('list'), '1 [ ] a (high) #x')


class F07Due(Base):
    def test_suffix(self):
        self.ok('add', 'a', '--due', '2026-03-01')
        self.assertEqual(self.ok('list'), '1 [ ] a due:2026-03-01')

    def test_all_suffixes_in_order(self):
        self.ok('add', 'a', '--priority', 'low', '--tag', 't', '--due', '2026-03-01')
        self.assertEqual(self.ok('list'), '1 [ ] a (low) #t due:2026-03-01')

    def test_invalid(self):
        self.assertEqual(self.bad('add', 'a', '--due', '2026-13-40'), 'Invalid date: 2026-13-40')
        self.assertEqual(self.bad('add', 'a', '--due', 'tomorrow'), 'Invalid date: tomorrow')

    def test_overdue(self):
        self.ok('add', 'past', '--due', '2026-01-10')
        self.ok('add', 'future', '--due', '2026-06-01')
        self.ok('add', 'nodue')
        self.ok('add', 'donepast', '--due', '2026-01-05')
        self.ok('done', '4')
        self.assertEqual(self.ok('list', '--overdue', '--today', '2026-02-01'),
                         '1 [ ] past due:2026-01-10')


class F08Edit(Base):
    def test_edit(self):
        self.ok('add', 'old')
        self.assertEqual(self.ok('edit', '1', '--title', 'New', 'title'), 'Edited 1')
        self.assertEqual(self.ok('list'), '1 [ ] New title')

    def test_unknown(self):
        self.assertEqual(self.bad('edit', '3', '--title', 'x'), 'No such task: 3')


class F09Search(Base):
    def test_search(self):
        self.ok('add', 'Buy Milk')
        self.ok('add', 'Walk dog')
        self.ok('add', 'milkshake', '--priority', 'low')
        self.assertEqual(self.ok('search', 'milk'), '1 [ ] Buy Milk\n3 [ ] milkshake (low)')

    def test_no_matches(self):
        self.ok('add', 'a')
        self.assertEqual(self.ok('search', 'zzz'), 'No matches')


class F10Export(Base):
    def seed(self):
        self.ok('add', 'a', '--priority', 'high', '--tag', 'x', '--tag', 'y', '--due', '2026-05-05')
        self.ok('add', 'b')
        self.ok('done', '2')

    def test_json(self):
        self.seed()
        data = json.loads(self.ok('export', '--format', 'json'))
        self.assertEqual(data, [
            {'id': 1, 'title': 'a', 'done': False, 'priority': 'high', 'tags': ['x', 'y'], 'due': '2026-05-05'},
            {'id': 2, 'title': 'b', 'done': True, 'priority': 'medium', 'tags': [], 'due': None}])

    def test_csv(self):
        self.seed()
        self.assertEqual(self.ok('export', '--format', 'csv'),
                         'id,title,done,priority,tags,due\n1,a,false,high,x;y,2026-05-05\n2,b,true,medium,,')

    def test_empty_json(self):
        self.assertEqual(json.loads(self.ok('export', '--format', 'json')), [])


class F11Stats(Base):
    def test_stats(self):
        self.assertEqual(self.ok('stats'), 'open: 0\ndone: 0\ntotal: 0')
        self.ok('add', 'a')
        self.ok('add', 'b')
        self.ok('add', 'c')
        self.ok('done', '1')
        self.ok('delete', '3')
        self.assertEqual(self.ok('stats'), 'open: 1\ndone: 1\ntotal: 2')


class F12Undo(Base):
    def test_nothing(self):
        self.assertEqual(self.bad('undo'), 'Nothing to undo')

    def test_undo_add_restores_next_id(self):
        self.ok('add', 'a')
        self.ok('add', 'b')
        self.assertEqual(self.ok('undo'), 'Undone')
        self.assertEqual(self.ok('list'), '1 [ ] a')
        self.assertEqual(self.ok('add', 'c'), 'Added 2')

    def test_undo_done_delete_edit_multi_level(self):
        self.ok('add', 'a')
        self.ok('done', '1')
        self.ok('edit', '1', '--title', 'z')
        self.ok('delete', '1')
        self.assertEqual(self.ok('list'), 'No tasks')
        self.ok('undo')
        self.assertEqual(self.ok('list'), '1 [x] z')
        self.ok('undo')
        self.assertEqual(self.ok('list'), '1 [x] a')
        self.ok('undo')
        self.assertEqual(self.ok('list'), '1 [ ] a')

    def test_failed_commands_do_not_count(self):
        self.ok('add', 'a')
        self.bad('done', '9')
        self.ok('undo')
        self.assertEqual(self.ok('list'), 'No tasks')


if __name__ == '__main__':
    unittest.main()
