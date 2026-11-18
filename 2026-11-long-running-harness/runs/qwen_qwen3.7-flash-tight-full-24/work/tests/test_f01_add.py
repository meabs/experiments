"""Tests for feature F01: add command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestF01Add(unittest.TestCase):
    """Test the add command - creates an open task and prints Added <id>."""

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

    def test_add_prints_added_id(self):
        """Running: add 'Buy milk' -> Output is 'Added 1'"""
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
        """Verify the JSON structure after adding"""
        self._run('add', 'Buy milk')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Buy milk')
        self.assertFalse(data['tasks'][0]['done'])
        self.assertEqual(data['next_id'], 2)


if __name__ == '__main__':
    unittest.main()
