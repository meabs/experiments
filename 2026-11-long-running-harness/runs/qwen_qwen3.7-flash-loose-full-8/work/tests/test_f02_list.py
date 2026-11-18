"""Tests for feature F02: list command."""
import json
import os
import subprocess
import shutil
import tempfile
import unittest


class TestList(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
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
    
    def test_empty_list(self):
        """Empty list prints 'No tasks'."""
        r = self._run('list')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), 'No tasks')
    
    def test_list_after_two_adds(self):
        """After two adds, lines show both tasks in id order."""
        self._run('add', 'Buy milk')
        self._run('add', 'Walk dog')
        r = self._run('list')
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '1 [ ] Buy milk')
        self.assertEqual(lines[1], '2 [ ] Walk dog')
    
    def test_list_order(self):
        """Tasks are listed in id order regardless of add order."""
        self._run('add', 'Third task')
        self._run('add', 'First task')
        self._run('add', 'Second task')
        r = self._run('list')
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split('\n')
        self.assertEqual(lines[0], '1 [ ] Third task')
        self.assertEqual(lines[1], '2 [ ] First task')
        self.assertEqual(lines[2], '3 [ ] Second task')


if __name__ == '__main__':
    unittest.main()
