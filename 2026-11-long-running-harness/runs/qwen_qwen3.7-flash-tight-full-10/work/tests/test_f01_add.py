"""Tests for Feature F01: add command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.script = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, *args):
        result = subprocess.run(
            ['python3', self.script] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir
        )
        return result

    def test_add_creates_task_and_prints_id(self):
        """Run: add 'Buy milk' -> Output is 'Added 1'"""
        r = self._run('add', 'Buy milk')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')

    def test_add_second_task_gets_id_2(self):
        """Run another add; output is 'Added 2'"""
        self._run('add', 'Buy milk')
        r = self._run('add', 'Walk dog')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 2')

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add"""
        self._run('add', 'Buy milk')
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))

    def test_tasks_json_content(self):
        """tasks.json has correct structure after add"""
        self._run('add', 'Buy milk')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        tasks = data['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['id'], 1)
        self.assertEqual(tasks[0]['title'], 'Buy milk')
        self.assertFalse(tasks[0]['done'])

    def test_next_id_increments(self):
        """After two adds, next_id is 3"""
        self._run('add', 'Buy milk')
        self._run('add', 'Walk dog')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        self.assertEqual(data['next_id'], 3)


if __name__ == '__main__':
    unittest.main()
