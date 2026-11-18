"""Tests for F01: add command"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

TASKS_PATH = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        shutil.copy2(TASKS_PATH, self.tmpdir)

    def _run(self, args):
        return subprocess.run(
            ['python3', 'tasks.py'] + args,
            capture_output=True, text=True, cwd=self.tmpdir
        )

    def test_add_single_task(self):
        r = self._run(['add', 'Buy milk'])
        self.assertEqual(r.stdout.strip(), 'Added 1')
        self.assertEqual(r.returncode, 0)

    def test_add_second_task_gets_id_2(self):
        self._run(['add', 'Buy milk'])
        r = self._run(['add', 'Walk dog'])
        self.assertEqual(r.stdout.strip(), 'Added 2')

    def test_tasks_json_created(self):
        self._run(['add', 'Test task'])
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))

    def test_tasks_json_valid(self):
        self._run(['add', 'Test task'])
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        self.assertIn('tasks', data)
        # JSON keys are strings
        self.assertIn('1', data['tasks'])
        self.assertEqual(data['tasks']['1']['title'], 'Test task')
        self.assertEqual(data['tasks']['1']['done'], False)
        self.assertEqual(data['next_id'], 2)


if __name__ == '__main__':
    unittest.main()
