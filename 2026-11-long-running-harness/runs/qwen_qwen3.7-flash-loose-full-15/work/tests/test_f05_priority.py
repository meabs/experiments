"""Tests for F05: priority feature"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF05Priority(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_add_high_priority_shows_suffix(self):
        r = self._run(['add', 'task a', '--priority', 'high'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a (high)')

    def test_add_low_priority_shows_suffix(self):
        r = self._run(['add', 'task a', '--priority', 'low'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a (low)')

    def test_default_priority_no_suffix(self):
        r = self._run(['add', 'task a'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] task a')

    def test_list_sort_priority_orders_correctly(self):
        self._run(['add', 'low task', '--priority', 'low'])
        self._run(['add', 'high task', '--priority', 'high'])
        self._run(['add', 'med task', '--priority', 'medium'])
        r = self._run(['list', '--sort', 'priority'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 3)
        self.assertIn('(high)', lines[0])
        self.assertNotIn('(high)', lines[1])
        self.assertIn('(low)', lines[2])

    def test_invalid_priority_exits_1(self):
        r = self._run(['add', 'task', '--priority', 'urgent'])
        self.assertEqual(r.stderr.strip(), 'Invalid priority: urgent')
        self.assertEqual(r.returncode, 1)

    def test_sort_priority_ties_by_id(self):
        self._run(['add', 'a', '--priority', 'high'])
        self._run(['add', 'b', '--priority', 'high'])
        self._run(['add', 'c', '--priority', 'high'])
        r = self._run(['list', '--sort', 'priority'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 3)
        # All high priority, should be in id order
        self.assertTrue(lines[0].startswith('1 '))
        self.assertTrue(lines[1].startswith('2 '))
        self.assertTrue(lines[2].startswith('3 '))


if __name__ == '__main__':
    unittest.main()
