"""Tests for feature F01: add command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestAdd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Copy tasks.py to the temp directory
        src = os.path.join(os.path.dirname(__file__), '..', 'tasks.py')
        shutil.copy2(src, self.tmpdir)
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def _run(self, *args):
        result = subprocess.run(
            ['python3', 'tasks.py'] + list(args),
            cwd=self.tmpdir,
            capture_output=True, text=True
        )
        return result
    
    def test_add_creates_task(self):
        """Running add 'Buy milk' outputs 'Added 1'."""
        r = self._run('add', 'Buy milk')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 1')
    
    def test_add_creates_second_task(self):
        """After two adds, second id is 2."""
        self._run('add', 'Buy milk')
        r = self._run('add', 'Walk dog')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'Added 2')
    
    def test_tasks_json_exists(self):
        """tasks.json exists after adding a task."""
        self._run('add', 'Buy milk')
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'tasks.json')))
    
    def test_tasks_json_content(self):
        """tasks.json contains the added task."""
        self._run('add', 'Buy milk')
        with open(os.path.join(self.tmpdir, 'tasks.json')) as f:
            data = json.load(f)
        self.assertEqual(data['next_id'], 2)
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Buy milk')
        self.assertFalse(data['tasks'][0]['done'])


if __name__ == '__main__':
    unittest.main()
