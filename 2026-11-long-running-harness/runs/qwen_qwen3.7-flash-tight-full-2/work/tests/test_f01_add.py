"""Tests for Feature F01: add command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Test suite for the 'add' command (Feature F01)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_py = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def run_tasks(self, *args):
        """Run tasks.py with given args and return (stdout, stderr, returncode)."""
        cmd = ['python3', self.tasks_py] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmpdir)
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def test_add_single_task(self):
        """add 'Buy milk' outputs 'Added 1'."""
        stdout, stderr, rc = self.run_tasks('add', 'Buy milk')
        self.assertEqual(rc, 0, f"Expected exit code 0, got {rc}. stderr: {stderr}")
        self.assertEqual(stdout, 'Added 1')

    def test_add_second_task(self):
        """After first add, second add outputs 'Added 2'."""
        self.run_tasks('add', 'Buy milk')
        stdout, stderr, rc = self.run_tasks('add', 'Walk dog')
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, 'Added 2')

    def test_tasks_json_exists(self):
        """tasks.json exists in cwd after add."""
        self.run_tasks('add', 'Buy milk')
        tasks_json = os.path.join(self.tmpdir, 'tasks.json')
        self.assertTrue(os.path.exists(tasks_json))

    def test_tasks_json_content(self):
        """tasks.json contains correct data after add."""
        self.run_tasks('add', 'Buy milk')
        tasks_json = os.path.join(self.tmpdir, 'tasks.json')
        with open(tasks_json) as f:
            data = json.load(f)
        self.assertEqual(len(data['tasks']), 1)
        task = data['tasks'][0]
        self.assertEqual(task['id'], 1)
        self.assertEqual(task['title'], 'Buy milk')
        self.assertFalse(task['done'])
        self.assertEqual(task['priority'], 'medium')
        self.assertEqual(task['tags'], [])
        self.assertIsNone(task['due'])
        self.assertEqual(data['next_id'], 2)

    def test_add_with_title_spaces(self):
        """add with multi-word title works correctly."""
        stdout, _, _ = self.run_tasks('add', 'Buy milk and eggs')
        self.assertEqual(stdout, 'Added 1')
        tasks_json = os.path.join(self.tmpdir, 'tasks.json')
        with open(tasks_json) as f:
            data = json.load(f)
        self.assertEqual(data['tasks'][0]['title'], 'Buy milk and eggs')


if __name__ == '__main__':
    unittest.main()
