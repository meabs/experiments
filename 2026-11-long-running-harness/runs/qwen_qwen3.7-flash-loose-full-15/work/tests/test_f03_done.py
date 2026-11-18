"""Tests for F03: done command"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF03Done(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_done_marks_task_done(self):
        self._run(['add', 'Buy milk'])
        r = self._run(['done', '1'])
        self.assertEqual(r.stdout.strip(), 'Done 1')
        self.assertEqual(r.returncode, 0)

    def test_done_shows_x_in_list(self):
        self._run(['add', 'Buy milk'])
        self._run(['done', '1'])
        r = self._run(['list'])
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], '1 [x] Buy milk')

    def test_done_unknown_id_exits_1(self):
        r = self._run(['done', '99'])
        self.assertEqual(r.stderr.strip(), 'No such task: 99')
        self.assertEqual(r.returncode, 1)

    def test_done_already_done_still_works(self):
        self._run(['add', 'Buy milk'])
        self._run(['done', '1'])
        r = self._run(['done', '1'])
        self.assertEqual(r.stdout.strip(), 'Done 1')
        self.assertEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
