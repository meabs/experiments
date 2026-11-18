"""Tests for F04: delete command"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF04Delete(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_delete_removes_task(self):
        self._run(['add', 'Buy milk'])
        self._run(['add', 'Walk dog'])
        r = self._run(['delete', '2'])
        self.assertEqual(r.stdout.strip(), 'Deleted 2')
        self.assertEqual(r.returncode, 0)

    def test_next_add_gets_new_id(self):
        self._run(['add', 'Buy milk'])
        self._run(['add', 'Walk dog'])
        self._run(['delete', '2'])
        r = self._run(['add', 'New task'])
        self.assertEqual(r.stdout.strip(), 'Added 3')

    def test_delete_unknown_id_exits_1(self):
        r = self._run(['delete', '99'])
        self.assertEqual(r.stderr.strip(), 'No such task: 99')
        self.assertEqual(r.returncode, 1)

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
