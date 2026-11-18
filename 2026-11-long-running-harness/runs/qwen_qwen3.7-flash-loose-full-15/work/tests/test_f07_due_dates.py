"""Tests for F07: due dates feature"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF07DueDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_add_with_due_date_shows_suffix(self):
        r = self._run(['add', 'task a', '--priority', 'low', '--tag', 't', '--due', '2026-03-01'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a (low) #t due:2026-03-01')

    def test_invalid_date_exits_1(self):
        r = self._run(['add', 'task a', '--due', '2026-13-40'])
        self.assertEqual(r.stderr.strip(), 'Invalid date: 2026-13-40')
        self.assertEqual(r.returncode, 1)

    def test_overdue_only_shows_open_tasks_before_today(self):
        self._run(['add', 'overdue task', '--due', '2020-01-01'])
        self._run(['add', 'future task', '--due', '2030-01-01'])
        self._run(['add', 'no due date task'])
        r = self._run(['list', '--overdue', '--today', '2025-01-01'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertIn('overdue task', lines[0])

    def test_overdue_does_not_show_done_tasks(self):
        self._run(['add', 'overdue task', '--due', '2020-01-01'])
        self._run(['done', '1'])
        r = self._run(['list', '--overdue', '--today', '2025-01-01'])
        self.assertEqual(r.stdout.strip(), 'No tasks')

    def test_suffix_order_priority_tags_due(self):
        r = self._run(['add', 'task a', '--priority', 'high', '--tag', 'x', '--tag', 'y', '--due', '2025-06-01'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a (high) #x #y due:2025-06-01')


if __name__ == '__main__':
    unittest.main()
