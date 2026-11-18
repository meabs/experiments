"""Tests for F02: list command"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF02List(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_empty_list(self):
        r = self._run(['list'])
        self.assertEqual(r.stdout.strip(), 'No tasks')
        self.assertEqual(r.returncode, 0)

    def test_list_two_tasks_in_order(self):
        self._run(['add', 'Buy milk'])
        self._run(['add', 'Walk dog'])
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')

    def test_list_shows_done_task(self):
        self._run(['add', 'Buy milk'])
        self._run(['done', '1'])
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '1 [x] Buy milk')

    def test_list_after_delete(self):
        self._run(['add', 'Buy milk'])
        self._run(['add', 'Walk dog'])
        self._run(['delete', '1'])
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '2 [ ] Walk dog')


if __name__ == '__main__':
    unittest.main()
